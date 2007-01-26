#-*- coding: utf-8 -*-

from distutils.core import setup, Extension
import pardus


setup(name="pardus",
      version=pardus.versionString(),
      description="Python Modules for Pardus",
      long_description="Python Modules for Pardus.",
      license="GNU GPL2",
      author="Barış Metin",
      author_email="baris@pardus.org.tr",
      url="http://www.pardus.org.tr/",
      packages = ['pardus', 'pardus.xorg'],
      ext_modules = [Extension('pardus.xorg.capslock',
                               sources=['pardus/xorg/capslock.c'],
                               libraries=['X11'])],
      )
