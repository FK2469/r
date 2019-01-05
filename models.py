# coding=utf-8
import os
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote
import uuid
from datetime import datetime
import hashlib

import cropresize2
import magic
import short_url
from PIL import Image
from flask import abort, request
from werkzeug.utils import cached_property

from ext import db
from mimes import IMAGE_MIMES, AUDIO_MIMES, VIDEO_MIMES
from config import UPLOAD_FOLDER


class PasteFile(db.Model):
    __tablename__ = "PasteFile"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(5000), nullable=False)
    filehash = db.Column(db.String(128), nullable=False, unique=True)
    uploadTime = db.Column(db.DateTime, nullable=False)
    mimetype = db.Column(db.String(256), nullable=False)
    filemd5 = db.Column(db.String(128), nullable=False, unique=True)

    # collation is for case-sensitive select
    # symlink = db.Column(
    #     db.String(50, collation='utf8_bin'), nullable=False, unique=True)
    size = db.Column(db.Integer, nullable=False)

    def __init__(self, filename="", mimetype="application/octet-stream",
                 size=0, filehash=None, symlink=None, filemd5=None):
        self.uploadTime = datetime.now()
        self.mimetype = mimetype
        self.size = int(size)
        self.filehash = filehash if filehash else self._hash_filename(filename)
        self.filename = filename if filename else self.filehash
        # self.symlink = symlink if symlink else self._gen_symlink()
        self.filemd5 = filemd5

    @staticmethod
    def _hash_filename(filename):
        _, _, suffix = filename.rpartition('.')
        return "%s.%s" % (uuid.uuid4().hex, suffix)

    # @staticmethod
    # def _gen_symlink():
    #     return "".join(choice(RANDOM_SEQ) for x in range(6))
    @cached_property
    def symlink(self):
        return short_url.encode_url(self.id)

    @classmethod
    def get_by_filehash(cls, filehash):
        return cls.query.filter_by(filehash=filehash).first()

    @classmethod
    def get_by_symlink(cls, symlink, code=404):
        id = short_url.decode_url(symlink)
        return cls.query.filter_by(id=id).first() or abort(code)
        # return cls.query.filter_by(symlink=symlink).first()

    @classmethod
    def get_by_md5(cls, filemd5):
        return cls.query.filter_by(filemd5=filemd5).first()

    @classmethod
    def create_by_uploadFile(cls, uploadedFile):
        rst = cls(uploadedFile.filename,
                  uploadedFile.mimetype, 0)
        uploadedFile.save(rst.path)
        duplicated = False
        corrupt = False
        filepath = None

        with open(rst.path, 'rb') as f:
            filemd5 = get_file_md5(f)
            uploadedFile = cls.get_by_md5(filemd5)

        if uploadedFile:
            filepath = os.path.join(UPLOAD_FOLDER, uploadedFile.filehash)
            if os.path.exists(filepath) or os.path.islink(filepath):
                duplicated = True
            else:
                corrupt = True

        if duplicated:
            os.remove(rst.path)
            return uploadedFile

        if corrupt:
            uploadedFile.filehash = rst.filehash
            return uploadedFile

        filestat = os.stat(rst.path)
        rst.size = filestat.st_size
        rst.filemd5 = filemd5
        return rst

    @classmethod
    def create_file_after_crop(cls, uploadedFile, width, height):
        assert uploadedFile.is_image, TypeError("Unsupported Image Type.")

        img = cropresize2.crop_resize(
            Image.open(uploadedFile), (int(width), int(height)))
        rst = cls(uploadedFile.filename,
                  uploadedFile.mimetype, 0)
        img.save(rst.path)

        filestat = os.stat(rst.path)
        rst.size = filestat.st_size

        return rst

    @classmethod
    def create_by_old_paste(cls, filehash, symlink):
        filepath = os.path.join(UPLOAD_FOLDER, filehash)
        mimetype = magic.from_file(filepath, mime=True)
        filestat = os.stat(filepath)
        size = filestat.st_size

        rst = cls(filehash, mimetype, size, filehash=filehash, symlink=symlink)
        return rst

    @property
    def path(self):
        return os.path.join(UPLOAD_FOLDER, self.filehash)

    @property
    def url_i(self):
        return "http://{host}/i/{filehash}".format(
            host=request.host, filehash=self.filehash)

    @property
    def url_p(self):
        return "http://{host}/p/{filehash}".format(
            host=request.host, filehash=self.filehash)

    @property
    def url_s(self):
        return "http://{host}/s/{symlink}".format(
            host=request.host, symlink=self.symlink)

    @property
    def url_d(self):
        return "http://{host}/d/{filehash}".format(
            host=request.host, filehash=self.filehash)

    @property
    def image_size(self):
        if self.is_image:
            im = Image.open(self.path)
            return im.size
        return (0, 0)

    @property
    def quoteurl(self):
        return quote(self.url_i)

    @classmethod
    def create_by_img(cls, img, filename, mimetype):
        rst = cls(filename, mimetype, 0)
        img.save(rst.path)
        filestat = os.stat(rst.path)
        rst.size = filestat.st_size
        return rst

    @classmethod
    def rsize(cls, oldPaste, weight, height):
        assert oldPaste.is_image

        img = cropresize2.crop_resize(
            Image.open(oldPaste.path), (int(weight), int(height)))

        return cls.create_by_img(img, oldPaste.filename, oldPaste.mimetype)

    @classmethod
    def affine(cls, oldPaste, w, h, a):
        assert oldPaste.is_image

        img_size = (int(w), int(h))
        img = Image.open(oldPaste.path).transform(
            img_size, Image.AFFINE, a, Image.BILINEAR)

        return cls.create_by_img(img, oldPaste.filename, oldPaste.mimetype)

    @property
    def is_image(self):
        return self.mimetype in IMAGE_MIMES

    @property
    def is_audio(self):
        return self.mimetype in AUDIO_MIMES

    @property
    def is_video(self):
        return self.mimetype in VIDEO_MIMES

    @property
    def is_pdf(self):
        return self.mimetype == "application/pdf"

    @property
    def size_humanize(self):
        if self.size < 1024:
            return "{0} bytes".format(self.size)
        size = self.size / 1024.0
        if size < 1024:
            size = "%.2f" % size
            return size.rstrip("0").rstrip(".") + " KB"
        size = size / 1024.0
        size = "%.2f" % size
        return size.rstrip("0").rstrip(".") + " MB"

    @property
    def type(self):
        may_types = ["image", "pdf", "video", "audio"]
        for t in may_types:
            if getattr(self, "is_" + t):
                return t
        return "binary"

    def simple_dict(self):
        return {
            "url_d": self.url_d,
            "url_i": self.url_i,
            "url_s": self.url_s,
            "url_p": self.url_p,
            "filename": self.filename,
            "size": self.size_humanize,
            "time": str(self.uploadTime),
            "type": self.type,
            "quoteurl": self.quoteurl,
        }


def get_file_md5(f, chunk_size=8192):
    h = hashlib.md5()
    while True:
        chunk = f.read(chunk_size)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()
