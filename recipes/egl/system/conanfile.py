from conan import ConanFile
from conan.errors import ConanException, ConanInvalidConfiguration
from conan.tools.system.package_manager import Apt, Yum, PacMan, Zypper, Pkg
from conan.tools.gnu.pkgconfig import PkgConfig


class SysConfigEGLConan(ConanFile):
    name = "egl"
    version = "system"
    description = "cross-platform virtual conan package for the EGL support"
    topics = ("conan", "opengl", "egl")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.khronos.org/egl"
    license = "MIT"
    settings = "os"

    def configure(self):
        if self.settings.os not in ["Linux", "FreeBSD"]:
            raise ConanInvalidConfiguration("This recipes supports only Linux and FreeBSD")
            
    # TODO: check how to do with system packages in Conan 2.0
    def package_info(self):
        self.info.header_only()

    def system_requirements(self):
        yum = Yum(self).install(["mesa-libEGL-devel"])
        try:
            # this works for ubuntu>=20, debian>=11, pop>=20
            apt = Apt(self).install(["libegl-dev"])
        except ConanException:
            apt = Apt(self).install(["libegl1-mesa-dev"])

        pacman = PacMan(self).install(["libglvnd"])
        zypper = Zypper(self).install(["Mesa-libEGL-devel"])
        pkg = Pkg(self).install(["libglvnd"])

        if all([True if result is None else False for result in [yum, apt, pacman, zypper, pkg]]):
            self.output.warn("Don't know how to install EGL for your distro.")

    def package_info(self):
        # TODO: Workaround for #2311 until a better solution can be found
        self.cpp_info.filenames["cmake_find_package"] = "egl_system"
        self.cpp_info.filenames["cmake_find_package_multi"] = "egl_system"

        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []

        pkg_config = PkgConfig(self, 'egl')
        pkg_config.fill_cpp_info(self.cpp_info, is_system=True)

        self.cpp_info.set_property("cmake_file_name", "egl_system")
        self.cpp_info.set_property("cmake_find_mode", "both")
