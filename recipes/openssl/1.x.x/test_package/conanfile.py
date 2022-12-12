from conan import ConanFile, conan_version
from conan.tools.scm import Version
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake, CMakeToolchain
import os

required_conan_version = ">=1.50.2 <1.51.0 || >=1.51.2"


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        if self.settings.os == "Android":
            tc.cache_variables["CONAN_LIBCXX"] = ""
        openssl = self.dependencies["openssl"]
        openssl_version = Version(openssl.ref.version)
        if openssl_version.major == "1" and openssl_version.minor == "1":
            tc.cache_variables["OPENSSL_WITH_ZLIB"] = False
        else:
            tc.cache_variables["OPENSSL_WITH_ZLIB"] = not openssl.options.no_zlib
        tc.generate()


    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindirs[0], "digest")
            self.run(bin_path, env="conanrun")
        if Version(conan_version).major >= 2:
            assert os.path.exists(os.path.join(self.dependencies["openssl"].package_folder, "licenses", "LICENSE"))
        else:
            assert os.path.exists(os.path.join(self.deps_cpp_info["openssl"].rootpath, "licenses", "LICENSE"))
