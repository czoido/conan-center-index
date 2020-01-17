import os

from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration


class LibXorgConan(ConanFile):
    name = "xorg"
    license = "X11"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.x.org/wiki/"
    description = "X.Org X Window System development libraries."
    settings = "os", "compiler", "build_type", "arch"
    options = {"skip_check": [True, False]}
    default_options = {"skip_check": False}
    _required_system_package = "xorg-dev"

    def system_requirements(self):
        installer = tools.SystemPackageTool()
        if not self.options.skip_check and not installer.installed(self._required_system_package):
            raise ConanInvalidConfiguration(
                "{0} system library missing. Install {0} in your system with something like: " \
                "sudo apt-get install {0}"
                    .format(self._required_system_package))
        elif self.options.skip_check:
            self.output.warn("Skipping check of xorg libraries installed on the system.")

    def configure(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration(
                "This library is only compatible with Linux")
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def package_info(self):
        self.cpp_info.includedirs.extend(
            ['/usr/include/xorg', '/usr/include/libdrm', '/usr/include/X11/dri'])
        self.cpp_info.libs.exted(['dmx', 'fontenc', 'FS', 'ICE', 'SM', 'X11', 'Xau', 'Xaw7', 'Xt',
                                  'Xcomposite', 'Xcursor', 'Xdamage', 'Xfixes', 'Xdmcp', 'Xext',
                                  'Xfont2', 'Xft', 'Xi', 'Xinerama', 'xkbfile', 'Xmu', 'Xmuu',
                                  'Xpm', 'Xrandr', 'Xrender', 'XRes', 'Xss', 'Xtst', 'Xv', 'XvMC',
                                  'Xxf86dga', 'Xxf86vm'])
        self.cpp_info.defines.extend(
            ['_DEFAULT_SOURCE', '_BSD_SOURCE', 'HAS_FCHOWN', 'HAS_STICKY_DIR_BIT'])
        self.cpp_info.cflags.append('visibility=hidden')

    def package_id(self):
        self.info.header_only()
