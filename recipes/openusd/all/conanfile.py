from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rm, rmdir, apply_conandata_patches, export_conandata_patches
import os
# mirror
required_conan_version = ">=2.1"

class OpenUSDConan(ConanFile):
    name = "openusd"
    description = "Universal Scene Description"
    license = "DocumentRef-LICENSE.txt:LicenseRef-Modified-Apache-2.0-License"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://openusd.org/"
    topics = ("3d", "scene", "usd")
    package_type = "shared-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_openimageio": [True, False],
        "with_materialx": [True, False],
    }
    default_options = {
        "with_openimageio": False,
        "with_materialx": False
    }

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("onetbb/2021.12.0", transitive_headers=True)
        self.requires("opensubdiv/3.6.0")
        self.requires("opengl/system")
        if self.options.with_openimageio:
            self.requires("openimageio/2.5.19.1")
        if self.options.with_materialx:
            self.requires("materialx/1.39.1")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.26 <5]")

    def validate(self):
        check_min_cppstd(self, 17)
        if self.options.with_materialx and not self.dependencies["materialx"].options.shared:
            raise ConanInvalidConfiguration('openusd requires -o "materialx/*:shared=True"')

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

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
        tc.cache_variables["PXR_BUILD_OPENIMAGEIO_PLUGIN"] = self.options.with_openimageio
        tc.cache_variables["PXR_ENABLE_MATERIALX_SUPPORT"] = self.options.with_materialx
        tc.cache_variables["TBB_tbb_LIBRARY"] = "TBB::tbb"
        tc.cache_variables["OIIO_LIBRARIES"] = "OpenImageIO::OpenImageIO" if self.options.with_openimageio else ""
        tc.generate()

        deps = CMakeDeps(self)
        subdiv_suffix = "" if self.dependencies["opensubdiv"].options.shared else "_static"
        deps.set_property("opensubdiv::osdcpu", "cmake_target_name", f"OpenSubdiv::osdCPU{subdiv_suffix}")
        deps.set_property("opensubdiv::osdgpu", "cmake_target_name", f"OpenSubdiv::osdGPU{subdiv_suffix}")

        # Remove materialx namespace
        materialx_targets = [
            "MaterialXCore",
            "MaterialXFormat",
            "MaterialXGenGlsl",
            "MaterialXGenOsl",
            "MaterialXGenMsl",
            "MaterialXGenShader",
            "MaterialXRender",
            "MaterialXRenderGlsl",
        ]
        for target in materialx_targets:
            deps.set_property(f"materialx::{target}", "cmake_target_name", target)
        deps.generate()

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
        def _add_library(name):
            self.cpp_info.components[name].libs = [f"usd_{name}"]
            if self.settings.os != "Windows":
                self.cpp_info.components[name].bindirs = ["lib"]
            return self.cpp_info.components[name]

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread", "dl"])

        kit_framework = "AppKit" if self.settings.os == "Macos" else "UIKit"

        _add_library("arch")
        _add_library("tf").requires = ["arch", "onetbb::libtbb"]
        _add_library("gf").requires = ["arch", "tf"]
        _add_library("pegtl").requires = ["arch"]
        _add_library("js").requires = ["tf"]
        _add_library("trace").requires = ["arch", "js", "tf", "onetbb::libtbb"]
        _add_library("work").requires = ["tf", "trace", "onetbb::libtbb"]
        _add_library("plug").requires = ["arch", "tf", "js", "trace", "work", "onetbb::libtbb"]
        _add_library("vt").requires = ["arch", "tf", "gf", "trace", "onetbb::libtbb"]
        _add_library("ts").requires = ["vt", "gf", "tf"]
        _add_library("ar").requires = ["arch", "js", "tf", "plug", "vt", "onetbb::libtbb"]
        _add_library("kind").requires = ["tf", "plug"]
        _add_library("sdf").requires = ["arch", "tf", "gf", "pegtl", "trace", "ts", "vt", "work", "ar", "onetbb::libtbb"]
        _add_library("sdr").requires = ["arch", "plug", "trace", "tf", "vt", "work", "ar", "sdf"]
        _add_library("pcp").requires = ["tf", "trace", "vt", "sdf", "work", "ar", "onetbb::libtbb"]
        _add_library("usd").requires = ["arch", "kind", "pcp", "sdf", "ar", "plug", "tf", "trace", "ts", "vt", "work", "onetbb::libtbb"]
        _add_library("usdGeom").requires = ["js", "tf", "plug", "vt", "sdf", "trace", "usd", "work", "onetbb::libtbb"]
        _add_library("usdVol").requires = ["usd", "sdf", "tf", "trace"]
        _add_library("usdMedia").requires = ["tf", "vt", "sdf", "usd", "usdGeom"]
        _add_library("usdShade").requires = ["tf", "vt", "js", "sdf", "sdr", "usd", "usdGeom", "onetbb::libtbb"]
        _add_library("usdLux").requires = ["tf", "vt", "sdf", "sdr", "usd", "usdGeom", "usdShade"]
        _add_library("usdProc").requires = ["tf", "usd", "usdGeom"]
        _add_library("usdRender").requires = ["gf", "tf", "usd", "usdGeom", "usdShade"]
        _add_library("usdHydra").requires = ["tf", "usd", "usdShade"]
        _add_library("usdRi").requires = ["tf", "vt", "sdf", "usd", "usdShade", "usdGeom"]
        _add_library("usdSemantics").requires = ["tf", "vt", "sdf", "usd", "usdGeom"]
        _add_library("usdSkel").requires = ["arch", "gf", "tf", "trace", "vt", "work", "sdf", "usd", "usdGeom", "onetbb::libtbb"]
        _add_library("usdUI").requires = ["tf", "vt", "sdf", "usd"]
        _add_library("usdUtils").requires = ["arch", "tf", "gf", "sdf", "usd", "usdGeom", "usdShade", "onetbb::libtbb"]
        _add_library("usdPhysics").requires = ["tf", "plug", "vt", "sdf", "trace", "usd", "usdGeom", "usdShade", "work"]
        _add_library("vdf").requires = ["arch", "gf", "tf", "trace", "vt", "work", "onetbb::libtbb"]
        _add_library("ef").requires = ["vdf", "arch", "tf", "trace", "usd", "work", "onetbb::libtbb"]
        _add_library("esf").requires = ["arch", "sdf", "tf", "vt", "usd"]
        _add_library("esfUsd").requires = ["arch", "esf", "tf", "sdf", "usd"]
        _add_library("exec").requires = ["ef", "esf", "tf", "trace", "ts", "sdf", "usd", "vdf", "vt", "onetbb::libtbb"]
        _add_library("execUsd").requires = ["esf", "esfUsd", "exec", "tf", "trace", "sdf", "usd"]
        _add_library("execGeom").requires = ["gf", "tf", "execUsd", "usdGeom"]
        _add_library("usdValidation").requires = ["sdf", "plug", "tf", "gf", "usd", "work"]
        _add_library("usdGeomValidators").requires = ["tf", "plug", "sdf", "usd", "usdGeom", "usdValidation"]
        _add_library("usdPhysicsValidators").requires = ["tf", "plug", "sdf", "usd", "usdGeom", "usdPhysics", "usdValidation"]
        _add_library("usdShadeValidators").requires = ["tf", "plug", "sdf", "usd", "sdr", "usdShade", "usdValidation"]
        _add_library("usdSkelValidators").requires = ["tf", "plug", "sdf", "usd", "usdSkel", "usdValidation"]
        _add_library("usdUtilsValidators").requires = ["tf", "plug", "sdf", "usd", "usdUtils", "usdValidation"]

        garch = _add_library("garch")
        garch.requires = ["arch", "tf", "opengl::opengl"]
        if is_apple_os(self):
            garch.frameworks = ["Foundation", kit_framework]

        _add_library("hf").requires = ["plug", "tf", "trace"]
        _add_library("hio").requires = ["arch", "js", "plug", "tf", "vt", "trace", "ar", "hf"]
        _add_library("cameraUtil").requires = ["tf", "gf"]
        _add_library("pxOsd").requires = ["tf", "gf", "vt", "opensubdiv::osdcpu"]
        _add_library("geomUtil").requires = ["arch", "gf", "tf", "vt", "pxOsd"]
        _add_library("glf").requires = ["ar", "arch", "garch", "gf", "hf", "hio", "plug", "tf", "trace", "sdf"]
        _add_library("hgi").requires = ["gf", "plug", "tf", "hio"]
        _add_library("hgiGL").requires = ["arch", "garch", "hf", "hgi", "tf", "trace"]

        if is_apple_os(self):
            hgiMetal = _add_library("hgiMetal")
            hgiMetal.requires = ["arch", "hgi", "tf", "trace"]
            hgiMetal.frameworks = ["Foundation", "Metal", kit_framework]

        hgiInterop = _add_library("hgiInterop")
        hgiInterop.requires = ["gf", "tf", "hgi", "vt", "garch"]
        if is_apple_os(self):
            hgiInterop.frameworks = ["Foundation", "CoreVideo"]
            hgiInterop.requires.append("hgiMetal")

        _add_library("hd").requires = ["plug", "tf", "trace", "vt", "work", "sdf", "cameraUtil", "hf", "pxOsd", "sdr", "onetbb::libtbb"]
        _add_library("hdar").requires = ["hd", "ar"]
        _add_library("hdGp").requires = ["hd", "hf", "onetbb::libtbb"]
        _add_library("hdsi").requires = ["plug", "tf", "trace", "vt", "work", "sdf", "cameraUtil", "geomUtil", "hf", "hd", "pxOsd", "onetbb::libtbb"]

        hdSt = _add_library("hdSt")
        hdSt.requires = ["hio", "garch", "glf", "hd", "hdsi", "hgiGL", "hgiInterop", "sdr", "tf", "trace", "onetbb::libtbb", "opensubdiv::osdcpu", "opensubdiv::osdgpu"]
        if self.options.with_materialx:
            hdSt.requires = ["hdMtlx", "materialx::MaterialXGenShader", "materialx::MaterialXRender", "materialx::MaterialXCore", "materialx::MaterialXFormat",
                                                         "materialx::MaterialXGenGlsl", "materialx::MaterialXGenMsl"]
        _add_library("hdx").requires = ["plug", "tf", "vt", "gf", "work", "garch", "glf", "pxOsd", "hd", "hdSt", "hgi", "hgiInterop", "cameraUtil", "sdf"]

        if self.options.with_materialx:
            _add_library("usdMtlx").requires = ["arch", "gf", "sdf", "sdr", "tf", "vt", "usd", "usdGeom", "usdShade", "usdUI", "usdUtils", "materialx::MaterialXCore", "materialx::MaterialXFormat"]
            _add_library("hdMtlx").requires = ["gf", "hd", "sdf", "sdr", "tf", "trace", "usdMtlx", "vt", "materialx::MaterialXCore", "materialx::MaterialXFormat"]
            _add_library("usdBakeMtlx").requires = ["tf", "sdr", "usdMtlx", "usdShade", "hd", "hdMtlx", "usdImaging", "materialx::MaterialXCore", "materialx::MaterialXFormat", "materialx::MaterialXRenderGlsl"]

        _add_library("usdImaging").requires = ["gf", "tf", "plug", "trace", "vt", "work", "geomUtil", "hd", "hdar", "hio", "pxOsd", "sdf", "usd", "usdGeom", "usdLux", "usdRender", "usdShade", "usdVol", "ar", "onetbb::libtbb"]
        _add_library("usdImagingGL").requires = ["gf", "tf", "plug", "trace", "vt", "work", "hio", "garch", "glf", "hd", "hdsi", "hdx", "pxOsd", "sdf", "sdr", "usd", "usdGeom", "usdHydra", "usdShade", "usdImaging", "ar"]
        _add_library("usdProcImaging").requires = ["usdImaging", "usdProc"]
        _add_library("usdRiPxrImaging").requires = ["gf", "tf", "plug", "trace", "vt", "work", "hd", "pxOsd", "sdf", "usd", "usdGeom", "usdLux", "usdShade", "usdImaging", "usdVol", "ar"]
        _add_library("usdSkelImaging").requires = ["hio", "hd", "usdImaging", "usdSkel"]
        _add_library("usdVolImaging").requires = ["usdImaging"]
        _add_library("usdAppUtils").requires = ["garch", "gf", "hio", "sdf", "tf", "usd", "usdGeom", "usdImagingGL"]

        # Plugins
        plugin_suffix = {
            "Windows": "",
            "Linux": ".so",
            "Macos": ".dylib"
        }.get(str(self.settings.os), "so")
        plugin_dir = os.path.join("plugin", "usd")

        self.cpp_info.components["hioAvif"].libs = [f"hioAvif{plugin_suffix}"]
        self.cpp_info.components["hioAvif"].libdirs = [plugin_dir]
        self.cpp_info.components["hioAvif"].bindirs = [plugin_dir]
        self.cpp_info.components["hioAvif"].requires = ["ar", "arch", "gf", "hio", "tf"]

        if is_apple_os(self):
            self.cpp_info.components["hioImageIO"].libs = [f"hioImageIO{plugin_suffix}"]
            self.cpp_info.components["hioImageIO"].libdirs = [plugin_dir]
            self.cpp_info.components["hioImageIO"].bindirs = [plugin_dir]
            self.cpp_info.components["hioImageIO"].requires = ["ar", "arch", "gf", "hio", "tf"]
            self.cpp_info.components["hioImageIO"].frameworks = ["Foundation", "ImageIO", "CoreGraphics"]

        if self.options.with_openimageio:
            self.cpp_info.components["hioOiio"].libs = [f"hioOiio{plugin_suffix}"]
            self.cpp_info.components["hioOiio"].libdirs = [plugin_dir]
            self.cpp_info.components["hioOiio"].bindirs = [plugin_dir]
            self.cpp_info.components["hioOiio"].requires = ["ar", "arch", "gf", "hio", "tf", "openimageio::openimageio"]

        if self.settings.os != "Windows":
            # This plugins are not exporting any symbols on windows
            self.cpp_info.components["hdStorm"].libs = [f"hdStorm{plugin_suffix}"]
            self.cpp_info.components["hdStorm"].libdirs = [plugin_dir]
            self.cpp_info.components["hdStorm"].bindirs = [plugin_dir]
            self.cpp_info.components["hdStorm"].requires = ["plug", "tf", "trace", "vt", "work", "hd", "hdSt", "opensubdiv::osdcpu", "opensubdiv::osdgpu"]

            self.cpp_info.components["sdrGlslfx"].libs = [f"sdrGlslfx{plugin_suffix}"]
            self.cpp_info.components["sdrGlslfx"].libdirs = [plugin_dir]
            self.cpp_info.components["sdrGlslfx"].bindirs = [plugin_dir]
            self.cpp_info.components["sdrGlslfx"].requires = ["ar", "sdr", "hio"]

            self.cpp_info.components["usdShaders"].libs = [f"usdShaders{plugin_suffix}"]
            self.cpp_info.components["usdShaders"].libdirs = [plugin_dir]
            self.cpp_info.components["usdShaders"].bindirs = [plugin_dir]
            self.cpp_info.components["usdShaders"].requires = ["ar", "sdr", "usdShade"]
