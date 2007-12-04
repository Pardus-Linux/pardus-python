#-*- coding: utf-8 -*-

import os.path
from distutils.core import setup, Extension
from distutils.command.install import install

import pardus

class Install(install):
    def finalize_options(self):
        # NOTE: for Pardus distribution
        if os.path.exists("/etc/pardus-release"):
            self.install_platlib = '$base/lib/pardus'
            self.install_purelib = '$base/lib/pardus'
        install.finalize_options(self)
    
    def run(self):
        install.run(self)

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
      cmdclass = {'install' : Install})
