#-*- coding: utf-8 -*-

from distutils.core import setup, Extension
import pmp


setup(name="pmp",
      version=pmp.versionString(),
      description="Python Modules for Pardus (PMP)",
      long_description="Python Modules for Pardus (PMP).",
      license="GNU GPL2",
      author="Barış Metin",
      author_email="baris@pardus.org.tr",
      url="http://www.pardus.org.tr/",
      packages = ['pmp', 'pmp.xorg'],
      ext_modules = [Extension('pmp.xorg.capslock',
                               sources=['pmp/xorg/capslock.c'],
                               libraries=['X11'])],
      )
