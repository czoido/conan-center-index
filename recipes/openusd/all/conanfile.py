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
        tc.cache_variables["PXR_USE_DEBUG_PYTHON"] = False
        tc.cache_variables["PXR_BUILD_USD_TOOLS"] = False

        tc.cache_variables["TBB_tbb_LIBRARY"] = "TBB::tbb"
        tc.generate()

        tc = CMakeDeps(self)
        subdiv_suffix = "" if self.dependencies["opensubdiv"].options.shared else "_static"
        tc.set_property("opensubdiv::osdcpu", "cmake_target_name", f"OpenSubdiv::osdCPU{subdiv_suffix}")
        tc.set_property("opensubdiv::osdgpu", "cmake_target_name", f"OpenSubdiv::osdGPU{subdiv_suffix}")
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
            self.cpp_info.system_libs.extend(["m", "pthread", "dl"])

        kit_framework = "AppKit" if self.settings.os == "Macos" else "UIKit"

        # Check
        self.cpp_info.components["arch"].libs = ["usd_arch"]

        # Check
        self.cpp_info.components["ar"].libs = ["usd_ar"]
        self.cpp_info.components["ar"].requires = ["vt", "plug", "work", "trace", "js", "gf", "tf", "arch"]
        self.cpp_info.components["ar"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["cameraUtil"].libs = ["usd_cameraUtil"]
        self.cpp_info.components["cameraUtil"].requires = ["gf", "tf", "arch"]

        # TODO: INTERFACE_SYSTEM_INCLUDE_DIRECTORIES and INTERFACE_INCLUDE_DIRECTORIES??
        self.cpp_info.components["ef"].libs = ["usd_ef"]
        self.cpp_info.components["ef"].requires = ["vdf", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["ef"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["esf"].libs = ["usd_esf"]
        self.cpp_info.components["esf"].requires = ["usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["esfUsd"].libs = ["usd_esfUsd"]
        self.cpp_info.components["esfUsd"].requires = ["esf", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # TODO: INTERFACE_SYSTEM_INCLUDE_DIRECTORIES and INTERFACE_INCLUDE_DIRECTORIES??
        self.cpp_info.components["exec"].libs = ["usd_exec"]
        self.cpp_info.components["exec"].requires = ["esf", "ef", "vdf", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["exec"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["execUsd"].libs = ["usd_execUsd"]
        self.cpp_info.components["execUsd"].requires = ["exec", "esfUsd", "esf", "ef", "vdf", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["execGeom"].libs = ["usd_execGeom"]
        self.cpp_info.components["execGeom"].requires = ["execUsd", "exec", "esfUsd", "esf", "ef", "vdf", "usdGeom", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["garch"].libs = ["usd_garch"]
        self.cpp_info.components["garch"].requires = ["arch", "tf"]
        self.cpp_info.components["garch"].requires.append("opengl::opengl")
        if is_apple_os(self):
            self.cpp_info.components["garch"].frameworks = ["Foundation", kit_framework]

        # Check
        self.cpp_info.components["geomUtil"].libs = ["usd_geomUtil"]
        self.cpp_info.components["geomUtil"].requires = ["pxOsd", "vt", "trace", "js", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["gf"].libs = ["usd_gf"]
        self.cpp_info.components["gf"].requires = ["arch", "tf"]

        # Check
        self.cpp_info.components["glf"].libs = ["usd_glf"]
        self.cpp_info.components["glf"].requires = ["hio", "hf", "garch", "sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["hd"].libs = ["usd_hd"]
        self.cpp_info.components["hd"].requires = ["pxOsd", "cameraUtil", "hf", "sdr", "sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["hd"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["hdar"].libs = ["usd_hdar"]
        self.cpp_info.components["hdar"].requires = ["hd", "pxOsd", "cameraUtil", "hf", "sdr", "sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["hdGp"].libs = ["usd_hdGp"]
        self.cpp_info.components["hdGp"].requires = ["hd", "pxOsd", "cameraUtil", "hf", "sdr", "sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["hdGp"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["hdsi"].libs = ["usd_hdsi"]
        self.cpp_info.components["hdsi"].requires = ["hd", "geomUtil", "pxOsd", "cameraUtil", "hf", "sdr", "sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["hdsi"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["hdSt"].libs = ["usd_hdSt"]
        self.cpp_info.components["hdSt"].requires = ["hdsi", "hd", "hgiInterop", "hgiMetal", "hgiGL", "hgi", "glf", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "garch", "sdr", "sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["hdSt"].requires.extend(["onetbb::libtbb", "opensubdiv::opensubdiv"])

        # Check
        self.cpp_info.components["hdx"].libs = ["usd_hdx"]
        self.cpp_info.components["hdx"].requires = ["hdSt", "hdsi", "hd", "hgiInterop", "hgiMetal", "hgiGL", "hgi", "glf", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "garch", "sdr", "sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["hf"].libs = ["usd_hf"]
        self.cpp_info.components["hf"].requires = ["plug", "work", "trace", "js", "tf", "arch"]

        # Check
        self.cpp_info.components["hgi"].libs = ["usd_hgi"]
        self.cpp_info.components["hgi"].requires = ["hio", "hf", "ar", "vt", "plug", "work", "trace", "js", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["hgiGL"].libs = ["usd_hgiGL"]
        self.cpp_info.components["hgiGL"].requires = ["hgi", "hio", "hf", "garch", "ar", "vt", "plug", "work", "trace", "js", "gf", "tf", "arch"]

        # Check
        if is_apple_os(self):
            self.cpp_info.components["hgiMetal"].libs = ["usd_hgiMetal"]
            self.cpp_info.components["hgiMetal"].requires = ["hgi", "hio", "hf", "ar", "vt", "plug", "work", "trace", "js", "gf", "tf", "arch"]
            self.cpp_info.components["hgiMetal"].frameworks = ["Foundation", "Metal", kit_framework]

        # Check
        self.cpp_info.components["hgiInterop"].libs = ["usd_hgiInterop"]
        self.cpp_info.components["hgiInterop"].requires = ["hgi", "hio", "hf", "garch", "ar", "vt", "plug", "work", "trace", "js", "gf", "tf", "arch"]
        self.cpp_info.components["hgiInterop"].frameworks = ["Foundation", "CoreVideo"]
        if is_apple_os(self):
            self.cpp_info.components["hgiInterop"].requires.append("hgiMetal")

        # Check
        self.cpp_info.components["hio"].libs = ["usd_hio"]
        self.cpp_info.components["hio"].requires = ["hf", "ar", "vt", "plug", "work", "trace", "js", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["js"].libs = ["usd_js"]
        self.cpp_info.components["js"].requires = ["tf", "arch"]

        # Check
        self.cpp_info.components["kind"].libs = ["usd_kind"]
        self.cpp_info.components["kind"].requires = ["plug", "work", "trace", "js", "tf", "arch"]

        # Check
        self.cpp_info.components["pcp"].libs = ["usd_pcp"]
        self.cpp_info.components["pcp"].requires = ["sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["pcp"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["pegtl"].libs = ["usd_pegtl"]
        self.cpp_info.components["pegtl"].requires = ["arch"]

        # Check
        self.cpp_info.components["plug"].libs = ["usd_plug"]
        self.cpp_info.components["plug"].requires = ["work", "trace", "js", "tf", "arch"]
        self.cpp_info.components["plug"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["pxOsd"].libs = ["usd_pxOsd"]
        self.cpp_info.components["pxOsd"].requires = ["vt", "trace", "js", "gf", "tf", "arch"]
        self.cpp_info.components["pxOsd"].requires.append("opensubdiv::opensubdiv")

        # Check
        self.cpp_info.components["sdf"].libs = ["usd_sdf"]
        self.cpp_info.components["sdf"].requires = ["ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["sdf"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["sdr"].libs = ["usd_sdr"]
        self.cpp_info.components["sdr"].requires = ["sdf", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["tf"].libs = ["usd_tf"]
        self.cpp_info.components["tf"].requires = ["arch"]
        self.cpp_info.components["tf"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["trace"].libs = ["usd_trace"]
        self.cpp_info.components["trace"].requires = ["js", "tf", "arch"]
        self.cpp_info.components["trace"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["ts"].libs = ["usd_ts"]
        self.cpp_info.components["ts"].requires = ["vt", "trace", "js", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usd"].libs = ["usd_usd"]
        self.cpp_info.components["usd"].requires = ["pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["usd"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usdAppUtils"].libs = ["usd_usdAppUtils"]
        self.cpp_info.components["usdAppUtils"].requires = ["usdImagingGL", "usdImaging", "hdx", "hdSt", "hdsi", "hdar", "hd", "hgiInterop", "hgiMetal", "hgiGL", "hgi", "glf", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "garch", "usdHydra", "usdRender", "usdLux", "usdShade", "usdVol", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdGeom"].libs = ["usd_usdGeom"]
        self.cpp_info.components["usdGeom"].requires = ["usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["usdGeom"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usdGeomValidators"].libs = ["usd_usdGeomValidators"]
        self.cpp_info.components["usdGeomValidators"].requires = ["usdValidation", "usdGeom", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdHydra"].libs = ["usd_usdHydra"]
        self.cpp_info.components["usdHydra"].requires = ["usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdImaging"].libs = ["usd_usdImaging"]
        self.cpp_info.components["usdImaging"].requires = ["hdar", "hd", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "usdRender", "usdLux", "usdShade", "usdVol", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf"]
        self.cpp_info.components["usdImaging"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usdImagingGL"].libs = ["usd_usdImagingGL"]
        self.cpp_info.components["usdImagingGL"].requires = ["usdImaging", "hdx", "hdSt", "hdsi", "hdar", "hd", "hgiInterop", "hgiMetal", "hgiGL", "hgi", "glf", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "garch", "usdHydra", "usdRender", "usdLux", "usdShade", "usdVol", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdLux"].libs = ["usd_usdLux"]
        self.cpp_info.components["usdLux"].requires = ["usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdMedia"].libs = ["usd_usdMedia"]
        self.cpp_info.components["usdMedia"].requires = ["usdGeom", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdPhysics"].libs = ["usd_usdPhysics"]
        self.cpp_info.components["usdPhysics"].requires = ["usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdPhysicsValidators"].libs = ["usd_usdPhysicsValidators"]
        self.cpp_info.components["usdPhysicsValidators"].requires = ["usdValidation", "usdPhysics", "usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdProc"].libs = ["usd_usdProc"]
        self.cpp_info.components["usdProc"].requires = ["usdGeom", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdProcImaging"].libs = ["usd_usdProcImaging"]
        self.cpp_info.components["usdProcImaging"].requires = ["usdImaging", "hdar", "hd", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "usdRender", "usdProc", "usdLux", "usdShade", "usdVol", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdRender"].libs = ["usd_usdRender"]
        self.cpp_info.components["usdRender"].requires = ["usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdRi"].libs = ["usd_usdRi"]
        self.cpp_info.components["usdRi"].requires = ["usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdRiPxrImaging"].libs = ["usd_usdRiPxrImaging"]
        self.cpp_info.components["usdRiPxrImaging"].requires = ["usdImaging", "hdar", "hd", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "usdRender", "usdLux", "usdShade", "usdVol", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdSemantics"].libs = ["usd_usdSemantics"]
        self.cpp_info.components["usdSemantics"].requires =["usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdShade"].libs = ["usd_usdShade"]
        self.cpp_info.components["usdShade"].requires = ["usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["usdShade"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usdShadeValidators"].libs = ["usd_usdShadeValidators"]
        self.cpp_info.components["usdShadeValidators"].requires = ["usdValidation", "usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdSkel"].libs = ["usd_usdSkel"]
        self.cpp_info.components["usdSkel"].requires = ["usdGeom", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["usdSkel"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usdSkelImaging"].libs = ["usd_usdSkelImaging"]
        self.cpp_info.components["usdSkelImaging"].requires = ["usdImaging", "hdar", "hd", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "usdSkel", "usdRender", "usdLux", "usdShade", "usdVol", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdSkelValidators"].libs = ["usd_usdSkelValidators"]
        self.cpp_info.components["usdSkelValidators"].requires = ["usdValidation", "usdSkel", "usdGeom", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdUI"].libs = ["usd_usdUI"]
        self.cpp_info.components["usdUI"].requires = ["usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdUtils"].libs = ["usd_usdUtils"]
        self.cpp_info.components["usdUtils"].requires = ["usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]
        self.cpp_info.components["usdUtils"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["usdUtilsValidators"].libs = ["usd_usdUtilsValidators"]
        self.cpp_info.components["usdUtilsValidators"].requires = ["usdValidation", "usdUtils", "usdShade", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdValidation"].libs = ["usd_usdValidation"]
        self.cpp_info.components["usdValidation"].requires = ["usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdVol"].libs = ["usd_usdVol"]
        self.cpp_info.components["usdVol"].requires = ["usdGeom", "usd", "pcp", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # Check
        self.cpp_info.components["usdVolImaging"].libs = ["usd_usdVolImaging"]
        self.cpp_info.components["usdVolImaging"].requires = ["usdImaging", "hdar", "hd", "geomUtil", "pxOsd", "cameraUtil", "hio", "hf", "usdRender", "usdLux", "usdShade", "usdVol", "usdGeom", "usd", "pcp", "sdr", "sdf", "kind", "ar", "ts", "vt", "plug", "work", "trace", "js", "pegtl", "gf", "tf", "arch"]

        # TODO: INTERFACE_SYSTEM_INCLUDE_DIRECTORIES and INTERFACE_INCLUDE_DIRECTORIES??
        self.cpp_info.components["vdf"].libs = ["usd_vdf"]
        self.cpp_info.components["vdf"].requires = ["vt", "work", "trace", "js", "gf", "tf", "arch"]
        self.cpp_info.components["vdf"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["vt"].libs = ["usd_vt"]
        self.cpp_info.components["vt"].requires = ["trace", "js", "gf", "tf", "arch"]
        self.cpp_info.components["vt"].requires.append("onetbb::libtbb")

        # Check
        self.cpp_info.components["work"].libs = ["usd_work"]
        self.cpp_info.components["work"].requires = ["trace", "js", "tf", "arch"]
        self.cpp_info.components["work"].requires.append("onetbb::libtbb")
