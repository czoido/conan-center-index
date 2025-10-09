from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rm, rmdir
import os

required_conan_version = ">=2.1"

class OpenUSDConan(ConanFile):
    name = "openusd"
    description = "Universal Scene Description"
    license = "DocumentRef-LICENSE.txt:LicenseRef-Modified-Apache-2.0-License"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://openusd.org/"
    topics = ("3d", "scene", "usd")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": False,
    }
    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("onetbb/2021.12.0", transitive_headers=True)
        self.requires("opensubdiv/3.6.0")
        self.requires("opengl/system")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.26 <5]")

    def validate(self):
        check_min_cppstd(self, 17)
        # Require same options as in https://github.com/PixarAnimationStudios/OpenUSD/blob/release/build_scripts/build_usd.py#L1450
        if not self.dependencies["opensubdiv"].options.with_tbb and self.options.shared:
            raise ConanInvalidConfiguration("openusd requires -o opensubdiv/*:with_tbb=True when building shared")
        if not self.dependencies["opensubdiv"].options.with_opengl:
            raise ConanInvalidConfiguration("openusd requires -o opensubdiv/*:with_opengl=True")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        # Use variables in documented in https://github.com/PixarAnimationStudios/OpenUSD/blob/release/BUILDING.md
        tc.cache_variables["PXR_BUILD_USDVIEW"] = False
        tc.cache_variables["PXR_BUILD_TESTS"] = False
        tc.cache_variables["PXR_BUILD_EXAMPLES"] = False
        tc.cache_variables["PXR_BUILD_TUTORIALS"] = False
        tc.cache_variables["PXR_BUILD_HTML_DOCUMENTATION"] = False
        tc.cache_variables["PXR_ENABLE_PYTHON_SUPPORT"] = False

        tc.cache_variables["OPENSUBDIV_LIBRARIES"] = "OpenSubdiv::osdcpu"
        tc.cache_variables["OPENSUBDIV_INCLUDE_DIR"] = self.dependencies['opensubdiv'].cpp_info.includedirs[0].replace("\\", "/")
        target_suffix = "" if self.dependencies["opensubdiv"].options.shared else "_static"
        tc.cache_variables["OPENSUBDIV_OSDCPU_LIBRARY"] = "OpenSubdiv::osdcpu"+target_suffix
        tc.cache_variables["TBB_tbb_LIBRARY"] = "TBB::tbb"
        tc.generate()

        tc = CMakeDeps(self)
        tc.set_property("opensubdiv::osdcpu", "cmake_target_name", "OpenSubdiv::osdcpu")
        tc.set_property("opensubdiv::osdcpu", "cmake_target_aliases", ["OpenSubdiv::osdcpu_static"])
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE.txt", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        rm(self, "pxrConfig.cmake", self.package_folder)
        rmdir(self, os.path.join(self.package_folder, "cmake"))

    def package_info(self):
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
            self.cpp_info.system_libs.append("pthread")
            self.cpp_info.system_libs.append("dl")

        kit_framework = "AppKit" if self.settings.os == "Macos" else "UIKit"

        # Check
        self.cpp_info.components["usd_arch"].libs = ["usd_arch"]

        # Check
        self.cpp_info.components["usd_ar"].libs = ["usd_ar"]
        self.cpp_info.components["usd_ar"].requires = ["usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_ar"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_cameraUtil"].libs = ["usd_cameraUtil"]
        self.cpp_info.components["usd_cameraUtil"].requires = ["usd_gf", "usd_tf", "usd_arch"]

        # TODO: INTERFACE_SYSTEM_INCLUDE_DIRECTORIES and INTERFACE_INCLUDE_DIRECTORIES??
        self.cpp_info.components["usd_ef"].libs = ["usd_ef"]
        self.cpp_info.components["usd_ef"].requires = ["usd_vdf", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_ef"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_esf"].libs = ["usd_esf"]
        self.cpp_info.components["usd_esf"].requires = ["usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_esfUsd"].libs = ["usd_esfUsd"]
        self.cpp_info.components["usd_esfUsd"].requires = ["usd_esf", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # TODO: INTERFACE_SYSTEM_INCLUDE_DIRECTORIES and INTERFACE_INCLUDE_DIRECTORIES??
        self.cpp_info.components["usd_exec"].libs = ["usd_exec"]
        self.cpp_info.components["usd_exec"].requires = ["usd_esf", "usd_ef", "usd_vdf", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_exec"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_execUsd"].libs = ["usd_execUsd"]
        self.cpp_info.components["usd_execUsd"].requires = ["usd_exec", "usd_esfUsd", "usd_esf", "usd_ef", "usd_vdf", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_execGeom"].libs = ["usd_execGeom"]
        self.cpp_info.components["usd_execGeom"].requires = ["usd_execUsd", "usd_exec", "usd_esfUsd", "usd_esf", "usd_ef", "usd_vdf", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_garch"].libs = ["usd_garch"]
        self.cpp_info.components["usd_garch"].requires = ["usd_arch", "usd_tf"]
        self.cpp_info.components["usd_garch"].requires.append("opengl::opengl")
        if is_apple_os(self):
            self.cpp_info.components["usd_garch"].frameworks = ["Foundation", kit_framework]

        # Check
        self.cpp_info.components["usd_geomUtil"].libs = ["usd_geomUtil"]
        self.cpp_info.components["usd_geomUtil"].requires = ["usd_pxOsd", "usd_vt", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_gf"].libs = ["usd_gf"]
        self.cpp_info.components["usd_gf"].requires = ["usd_arch", "usd_tf"]

        # Check
        self.cpp_info.components["usd_glf"].libs = ["usd_glf"]
        self.cpp_info.components["usd_glf"].requires = ["usd_hio", "usd_hf", "usd_garch", "usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_hd"].libs = ["usd_hd"]
        self.cpp_info.components["usd_hd"].requires = ["usd_pxOsd", "usd_cameraUtil", "usd_hf", "usd_sdr", "usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_hd"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_hdar"].libs = ["usd_hdar"]
        self.cpp_info.components["usd_hdar"].requires = ["usd_hd", "usd_pxOsd", "usd_cameraUtil", "usd_hf", "usd_sdr", "usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_hdGp"].libs = ["usd_hdGp"]
        self.cpp_info.components["usd_hdGp"].requires = ["usd_hd", "usd_pxOsd", "usd_cameraUtil", "usd_hf", "usd_sdr", "usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_hdGp"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_hdsi"].libs = ["usd_hdsi"]
        self.cpp_info.components["usd_hdsi"].requires = ["usd_hd", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hf", "usd_sdr", "usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_hdsi"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_hdSt"].libs = ["usd_hdSt"]
        self.cpp_info.components["usd_hdSt"].requires = ["usd_hdsi", "usd_hd", "usd_hgiInterop", "usd_hgiMetal", "usd_hgiGL", "usd_hgi", "usd_glf", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_garch", "usd_sdr", "usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_hdSt"].requires.extend(["onetbb::libtbb", "opensubdiv::opensubdiv"])

        # Check
        self.cpp_info.components["usd_hdx"].libs = ["usd_hdx"]
        self.cpp_info.components["usd_hdx"].requires = ["usd_hdSt", "usd_hdsi", "usd_hd", "usd_hgiInterop", "usd_hgiMetal", "usd_hgiGL", "usd_hgi", "usd_glf", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_garch", "usd_sdr", "usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_hf"].libs = ["usd_hf"]
        self.cpp_info.components["usd_hf"].requires = ["usd_plug", "usd_work", "usd_trace", "usd_js", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_hgi"].libs = ["usd_hgi"]
        self.cpp_info.components["usd_hgi"].requires = ["usd_hio", "usd_hf", "usd_ar", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_hgiGL"].libs = ["usd_hgiGL"]
        self.cpp_info.components["usd_hgiGL"].requires = ["usd_hgi", "usd_hio", "usd_hf", "usd_garch", "usd_ar", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        if is_apple_os(self):
            self.cpp_info.components["usd_hgiMetal"].libs = ["usd_hgiMetal"]
            self.cpp_info.components["usd_hgiMetal"].requires = ["usd_hgi", "usd_hio", "usd_hf", "usd_ar", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]
            self.cpp_info.components["usd_hgiMetal"].frameworks = ["Foundation", "Metal", kit_framework]

        # Check
        self.cpp_info.components["usd_hgiInterop"].libs = ["usd_hgiInterop"]
        self.cpp_info.components["usd_hgiInterop"].requires = ["usd_hgi", "usd_hio", "usd_hf", "usd_garch", "usd_ar", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_hgiInterop"].frameworks = ["Foundation", "CoreVideo"]
        if is_apple_os(self):
            self.cpp_info.components["usd_hgiInterop"].requires.append("usd_hgiMetal")

        # Check
        self.cpp_info.components["usd_hio"].libs = ["usd_hio"]
        self.cpp_info.components["usd_hio"].requires = ["usd_hf", "usd_ar", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_js"].libs = ["usd_js"]
        self.cpp_info.components["usd_js"].requires = ["usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_kind"].libs = ["usd_kind"]
        self.cpp_info.components["usd_kind"].requires = ["usd_plug", "usd_work", "usd_trace", "usd_js", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_pcp"].libs = ["usd_pcp"]
        self.cpp_info.components["usd_pcp"].requires = ["usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_pcp"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_pegtl"].libs = ["usd_pegtl"]
        self.cpp_info.components["usd_pegtl"].requires = ["usd_arch"]

        # Check
        self.cpp_info.components["usd_plug"].libs = ["usd_plug"]
        self.cpp_info.components["usd_plug"].requires = ["usd_work", "usd_trace", "usd_js", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_plug"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_pxOsd"].libs = ["usd_pxOsd"]
        self.cpp_info.components["usd_pxOsd"].requires = ["usd_vt", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_pxOsd"].requires.append("opensubdiv::opensubdiv")

        # Check
        self.cpp_info.components["usd_sdf"].libs = ["usd_sdf"]
        self.cpp_info.components["usd_sdf"].requires = ["usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_sdf"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_sdr"].libs = ["usd_sdr"]
        self.cpp_info.components["usd_sdr"].requires = ["usd_sdf", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_tf"].libs = ["usd_tf"]
        self.cpp_info.components["usd_tf"].requires = ["usd_arch"]
        self.cpp_info.components["usd_tf"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_trace"].libs = ["usd_trace"]
        self.cpp_info.components["usd_trace"].requires = ["usd_js", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_trace"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_ts"].libs = ["usd_ts"]
        self.cpp_info.components["usd_ts"].requires = ["usd_vt", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usd"].libs = ["usd_usd"]
        self.cpp_info.components["usd_usd"].requires = ["usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_usd"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_usdAppUtils"].libs = ["usd_usdAppUtils"]
        self.cpp_info.components["usd_usdAppUtils"].requires = ["usd_usdImagingGL", "usd_usdImaging", "usd_hdx", "usd_hdSt", "usd_hdsi", "usd_hdar", "usd_hd", "usd_hgiInterop", "usd_hgiMetal", "usd_hgiGL", "usd_hgi", "usd_glf", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_garch", "usd_usdHydra", "usd_usdRender", "usd_usdLux", "usd_usdShade", "usd_usdVol", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdGeom"].libs = ["usd_usdGeom"]
        self.cpp_info.components["usd_usdGeom"].requires = ["usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_usdGeom"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_usdGeomValidators"].libs = ["usd_usdGeomValidators"]
        self.cpp_info.components["usd_usdGeomValidators"].requires = ["usd_usdValidation", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdHydra"].libs = ["usd_usdHydra"]
        self.cpp_info.components["usd_usdHydra"].requires = ["usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdImaging"].libs = ["usd_usdImaging"]
        self.cpp_info.components["usd_usdImaging"].requires = ["usd_hdar", "usd_hd", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_usdRender", "usd_usdLux", "usd_usdShade", "usd_usdVol", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf"]
        self.cpp_info.components["usd_usdImaging"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_usdImagingGL"].libs = ["usd_usdImagingGL"]
        self.cpp_info.components["usd_usdImagingGL"].requires = ["usd_usdImaging", "usd_hdx", "usd_hdSt", "usd_hdsi", "usd_hdar", "usd_hd", "usd_hgiInterop", "usd_hgiMetal", "usd_hgiGL", "usd_hgi", "usd_glf", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_garch", "usd_usdHydra", "usd_usdRender", "usd_usdLux", "usd_usdShade", "usd_usdVol", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdLux"].libs = ["usd_usdLux"]
        self.cpp_info.components["usd_usdLux"].requires = ["usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdMedia"].libs = ["usd_usdMedia"]
        self.cpp_info.components["usd_usdMedia"].requires = ["usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdPhysics"].libs = ["usd_usdPhysics"]
        self.cpp_info.components["usd_usdPhysics"].requires = ["usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdPhysicsValidators"].libs = ["usd_usdPhysicsValidators"]
        self.cpp_info.components["usd_usdPhysicsValidators"].requires = ["usd_usdValidation", "usd_usdPhysics", "usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdProc"].libs = ["usd_usdProc"]
        self.cpp_info.components["usd_usdProc"].requires = ["usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdProcImaging"].libs = ["usd_usdProcImaging"]
        self.cpp_info.components["usd_usdProcImaging"].requires = ["usd_usdImaging", "usd_hdar", "usd_hd", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_usdRender", "usd_usdProc", "usd_usdLux", "usd_usdShade", "usd_usdVol", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdRender"].libs = ["usd_usdRender"]
        self.cpp_info.components["usd_usdRender"].requires = ["usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdRi"].libs = ["usd_usdRi"]
        self.cpp_info.components["usd_usdRi"].requires = ["usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdRiPxrImaging"].libs = ["usd_usdRiPxrImaging"]
        self.cpp_info.components["usd_usdRiPxrImaging"].requires = ["usd_usdImaging", "usd_hdar", "usd_hd", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_usdRender", "usd_usdLux", "usd_usdShade", "usd_usdVol", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdSemantics"].libs = ["usd_usdSemantics"]
        self.cpp_info.components["usd_usdSemantics"].requires =["usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdShade"].libs = ["usd_usdShade"]
        self.cpp_info.components["usd_usdShade"].requires = ["usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_usdShade"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_usdShadeValidators"].libs = ["usd_usdShadeValidators"]
        self.cpp_info.components["usd_usdShadeValidators"].libs = ["usd_usdValidation", "usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdSkel"].libs = ["usd_usdSkel"]
        self.cpp_info.components["usd_usdSkel"].requires = ["usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_usdSkel"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_usdSkelImaging"].libs = ["usd_usdSkelImaging"]
        self.cpp_info.components["usd_usdSkelImaging"].requires = ["usd_usdImaging", "usd_hdar", "usd_hd", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_usdSkel", "usd_usdRender", "usd_usdLux", "usd_usdShade", "usd_usdVol", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdSkelValidators"].libs = ["usd_usdSkelValidators"]
        self.cpp_info.components["usd_usdSkelValidators"].requires = ["usd_usdValidation", "usd_usdSkel", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdUI"].libs = ["usd_usdUI"]
        self.cpp_info.components["usd_usdUI"].requires = ["usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdUtils"].libs = ["usd_usdUtils"]
        self.cpp_info.components["usd_usdUtils"].requires = ["usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_usdUtils"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_usdUtilsValidators"].libs = ["usd_usdUtilsValidators"]
        self.cpp_info.components["usd_usdUtilsValidators"].requires = ["usd_usdValidation", "usd_usdUtils", "usd_usdShade", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdValidation"].libs = ["usd_usdValidation"]
        self.cpp_info.components["usd_usdValidation"].requires = ["usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdVol"].libs = ["usd_usdVol"]
        self.cpp_info.components["usd_usdVol"].requires = ["usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # Check
        self.cpp_info.components["usd_usdVolImaging"].libs = ["usd_usdVolImaging"]
        self.cpp_info.components["usd_usdVolImaging"].requires = ["usd_usdImaging", "usd_hdar", "usd_hd", "usd_geomUtil", "usd_pxOsd", "usd_cameraUtil", "usd_hio", "usd_hf", "usd_usdRender", "usd_usdLux", "usd_usdShade", "usd_usdVol", "usd_usdGeom", "usd_usd", "usd_pcp", "usd_sdr", "usd_sdf", "usd_kind", "usd_ar", "usd_ts", "usd_vt", "usd_plug", "usd_work", "usd_trace", "usd_js", "usd_pegtl", "usd_gf", "usd_tf", "usd_arch"]

        # TODO: INTERFACE_SYSTEM_INCLUDE_DIRECTORIES and INTERFACE_INCLUDE_DIRECTORIES??
        self.cpp_info.components["usd_vdf"].libs = ["usd_vdf"]
        self.cpp_info.components["usd_vdf"].requires = ["usd_vt", "usd_work", "usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_vdf"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_vt"].libs = ["usd_vt"]
        self.cpp_info.components["usd_vt"].requires = ["usd_trace", "usd_js", "usd_gf", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_vt"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usd_work"].libs = ["usd_work"]
        self.cpp_info.components["usd_work"].requires = ["usd_trace", "usd_js", "usd_tf", "usd_arch"]
        self.cpp_info.components["usd_work"].requires.append("onetbb::libtbb")
