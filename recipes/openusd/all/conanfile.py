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
        "with_openimageio": True,
        "with_materialx": True
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
        self.tool_requires("cmake/[>=3.26]")

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

    @property
    def components_info(self):
        is_apple = is_apple_os(self)
        kit_framework = "AppKit" if self.settings.os == "Macos" else "UIKit"
        plugin_suffix = {
            # Windows searches for libname without lib prefix, which works for the plugin naming scheme,
            # No need to declare the extensions and force a specific file name then as with the other OSs
            "Windows": "",
            "Linux": ".so",
            "Macos": ".dylib"
        }.get(str(self.settings.os), "so")
        plugin_dir = os.path.join("plugin", "usd")
        return {
            "arch": {},
            "tf": {
                "requires": ["arch", "onetbb::libtbb"]
            },
            "gf": {
                "requires": ["arch", "tf"]
            },
            "pegtl": {
                "requires": ["arch"]
            },
            "js": {
                "requires": ["tf"]
            },
            "trace": {
                "requires": ["arch", "js", "tf", "onetbb::libtbb"]
            },
            "work": {
                "requires": ["tf", "trace", "onetbb::libtbb"]
            },
            "plug": {
                "requires": ["arch", "tf", "js", "trace", "work", "onetbb::libtbb"]
            },
            "vt": {
                "requires": ["arch", "tf", "gf", "trace", "onetbb::libtbb"]
            },
            "ts": {
                "requires": ["vt", "gf", "tf"]
            },
            "ar": {
                "requires": ["arch", "js", "tf", "plug", "vt", "onetbb::libtbb"]
            },
            "kind": {
                "requires": ["tf", "plug"]
            },
            "sdf": {
                "requires": ["arch", "tf", "gf", "pegtl", "trace", "ts", "vt", "work", "ar", "onetbb::libtbb"]
            },
            "sdr": {
                "requires": ["arch", "plug", "trace", "tf", "vt", "work", "ar", "sdf"]
            },
            "pcp": {
                "requires": ["tf", "trace", "vt", "sdf", "work", "ar", "onetbb::libtbb"]
            },
            "usd": {
                "requires": ["arch", "kind", "pcp", "sdf", "ar", "plug", "tf", "trace", "ts", "vt", "work", "onetbb::libtbb"]
            },
            "usdGeom": {
                "requires": ["js", "tf", "plug", "vt", "sdf", "trace", "usd", "work", "onetbb::libtbb"]
            },
            "usdVol": {
                "requires": ["usd", "sdf", "tf", "trace"]
            },
            "usdMedia": {
                "requires": ["tf", "vt", "sdf", "usd", "usdGeom"]
            },
            "usdShade": {
                "requires": ["tf", "vt", "js", "sdf", "sdr", "usd", "usdGeom", "onetbb::libtbb"]
            },
            "usdLux": {
                "requires": ["tf", "vt", "sdf", "sdr", "usd", "usdGeom", "usdShade"]
            },
            "usdProc": {
                "requires": ["tf", "usd", "usdGeom"]
            },
            "usdRender": {
                "requires": ["gf", "tf", "usd", "usdGeom", "usdShade"]
            },
            "usdHydra": {
                "requires": ["tf", "usd", "usdShade"]
            },
            "usdRi": {
                "requires": ["tf", "vt", "sdf", "usd", "usdShade", "usdGeom"]
            },
            "usdSemantics": {
                "requires": ["tf", "vt", "sdf", "usd", "usdGeom"]
            },
            "usdSkel": {
                "requires": ["arch", "gf", "tf", "trace", "vt", "work", "sdf", "usd", "usdGeom", "onetbb::libtbb"]
            },
            "usdUI": {
                "requires": ["tf", "vt", "sdf", "usd"]
            },
            "usdUtils": {
                "requires": ["arch", "tf", "gf", "sdf", "usd", "usdGeom", "usdShade", "onetbb::libtbb"]
            },
            "usdPhysics": {
                "requires": ["tf", "plug", "vt", "sdf", "trace", "usd", "usdGeom", "usdShade", "work"]
            },
            "vdf": {
                "requires": ["arch", "gf", "tf", "trace", "vt", "work", "onetbb::libtbb"]
            },
            "ef": {
                "requires": ["vdf", "arch", "tf", "trace", "usd", "work", "onetbb::libtbb"]
            },
            "esf": {
                "requires": ["arch", "sdf", "tf", "vt", "usd"]
            },
            "esfUsd": {
                "requires": ["arch", "esf", "tf", "sdf", "usd"]
            },
            "exec": {
                "requires": ["ef", "esf", "tf", "trace", "ts", "sdf", "usd", "vdf", "vt", "onetbb::libtbb"]
            },
            "execUsd": {
                "requires": ["esf", "esfUsd", "exec", "tf", "trace", "sdf", "usd"]
            },
            "execGeom": {
                "requires": ["gf", "tf", "execUsd", "usdGeom"]
            },
            "usdValidation": {
                "requires": ["sdf", "plug", "tf", "gf", "usd", "work"]
            },
            "usdGeomValidators": {
                "requires": ["tf", "plug", "sdf", "usd", "usdGeom", "usdValidation"]
            },
            "usdPhysicsValidators": {
                "requires": ["tf", "plug", "sdf", "usd", "usdGeom", "usdPhysics", "usdValidation"]
            },
            "usdShadeValidators": {
                "requires": ["tf", "plug", "sdf", "usd", "sdr", "usdShade", "usdValidation"]
            },
            "usdSkelValidators": {
                "requires": ["tf", "plug", "sdf", "usd", "usdSkel", "usdValidation"]
            },
            "usdUtilsValidators": {
                "requires": ["tf", "plug", "sdf", "usd", "usdUtils", "usdValidation"]
            },
            "garch": {
                "requires": ["arch", "tf", "opengl::opengl"],
                "frameworks": ["Foundation", kit_framework]
            },
            "hf": {
                "requires": ["plug", "tf", "trace"]
            },
            "hio": {
                "requires": ["arch", "js", "plug", "tf", "vt", "trace", "ar", "hf"]
            },
            "cameraUtil": {
                "requires": ["tf", "gf"]
            },
            "pxOsd": {
                "requires": ["tf", "gf", "vt", "opensubdiv::osdcpu"]
            },
            "geomUtil": {
                "requires": ["arch", "gf", "tf", "vt", "pxOsd"]
            },
            "glf": {
                "requires": ["ar", "arch", "garch", "gf", "hf", "hio", "plug", "tf", "trace", "sdf"]
            },
            "hgi": {
                "requires": ["gf", "plug", "tf", "hio"]
            },
            "hgiGL": {
                "requires": ["arch", "garch", "hf", "hgi", "tf", "trace"]
            },
            "hgiMetal": {
                "condition": is_apple,
                "requires": ["arch", "hgi", "tf", "trace"],
                "frameworks": ["Foundation", "Metal", kit_framework]
            },
            "hgiInterop": {
                "requires": ["gf", "tf", "hgi", "vt", "garch"] + (["hgiMetal"] if is_apple else []),
                "frameworks": ["Foundation", "CoreVideo"]
            },
            "hd": {
                "requires": ["plug", "tf", "trace", "vt", "work", "sdf", "cameraUtil",
                             "hf", "pxOsd", "sdr", "onetbb::libtbb"]
            },
            "hdar": {
                "requires": ["hd", "ar"]
            },
            "hdGp": {
                "requires": ["hd", "hf", "onetbb::libtbb"]
            },
            "hdsi": {
                "requires": ["plug", "tf", "trace", "vt", "work", "sdf", "cameraUtil",
                             "geomUtil", "hf", "hd", "pxOsd", "onetbb::libtbb"]
            },
            "hdSt": {
                "requires": ["hdMtlx", "materialx::MaterialXGenShader", "materialx::MaterialXRender",
                             "materialx::MaterialXCore", "materialx::MaterialXFormat",
                             "materialx::MaterialXGenGlsl", "materialx::MaterialXGenMsl"] if self.options.with_materialx else
                            ["hio", "garch", "glf", "hd", "hdsi", "hgiGL", "hgiInterop", "sdr",
                             "tf", "trace", "onetbb::libtbb", "opensubdiv::osdcpu", "opensubdiv::osdgpu"]
            },
            "hdx": {
                "requires": ["plug", "tf", "vt", "gf", "work", "garch", "glf", "pxOsd", "hd",
                             "hdSt", "hgi", "hgiInterop", "cameraUtil", "sdf"]
            },
            "usdMtlx": {
                "condition": self.options.with_materialx,
                "requires": ["arch", "gf", "sdf", "sdr", "tf", "vt", "usd", "usdGeom", "usdShade", "usdUI",
                             "usdUtils", "materialx::MaterialXCore", "materialx::MaterialXFormat"]
            },
            "hdMtlx": {
                "condition": self.options.with_materialx,
                "requires": ["gf", "hd", "sdf", "sdr", "tf", "trace", "usdMtlx", "vt",
                             "materialx::MaterialXCore", "materialx::MaterialXFormat"]
            },
            "usdBakeMtlx": {
                "condition": self.options.with_materialx,
                "requires": ["tf", "sdr", "usdMtlx", "usdShade", "hd", "hdMtlx", "usdImaging", "materialx::MaterialXCore",
                             "materialx::MaterialXFormat", "materialx::MaterialXRenderGlsl"]
            },
            "usdImaging": {
                "requires": ["gf", "tf", "plug", "trace", "vt", "work", "geomUtil", "hd", "hdar", "hio", "pxOsd", "sdf", "usd",
                             "usdGeom", "usdLux", "usdRender", "usdShade", "usdVol", "ar", "onetbb::libtbb"]
            },
            "usdImagingGL": {
                "requires": ["gf", "tf", "plug", "trace", "vt", "work", "hio", "garch", "glf", "hd", "hdsi", "hdx", "pxOsd",
                             "sdf", "sdr", "usd", "usdGeom", "usdHydra", "usdShade", "usdImaging", "ar"]
            },
            "usdProcImaging": {
                "requires": ["usdImaging", "usdProc"]
            },
            "usdRiPxrImaging": {
                "requires": ["gf", "tf", "plug", "trace", "vt", "work", "hd", "pxOsd", "sdf", "usd", "usdGeom", "usdLux", "usdShade", "usdImaging", "usdVol", "ar"]
            },
            "usdSkelImaging": {
                "requires": ["hio", "hd", "usdImaging", "usdSkel"]
            },
            "usdVolImaging": {
                "requires": ["usdImaging"]
            },
            "usdAppUtils": {
                "requires": ["garch", "gf", "hio", "sdf", "tf", "usd", "usdGeom", "usdImagingGL"]
            },
            # Plugins
            "hioAvif": {
                "libs": [f"hioAvif{plugin_suffix}"],
                "libdirs": [plugin_dir],
                "bindirs": [plugin_dir],
                "requires": ["ar", "arch", "gf", "hio", "tf"],
                "system_libs": []
            },
            "hioImageIO": {
                "condition": is_apple,
                "libs": [f"hioImageIO{plugin_suffix}"],
                "libdirs": [plugin_dir],
                "bindirs": [plugin_dir],
                "requires": ["ar", "arch", "gf", "hio", "tf"],
                "frameworks": ["Foundation", "ImageIO", "CoreGraphics"],
                "system_libs": []
            },
            "hioOiio": {
                "condition": self.options.with_openimageio,
                "libs": [f"hioOiio{plugin_suffix}"],
                "libdirs": [plugin_dir],
                "bindirs": [plugin_dir],
                "requires": ["ar", "arch", "gf", "hio", "tf", "openimageio::openimageio"],
                "system_libs": []
            },
            "hdStorm": {
                "condition": self.settings.os != "Windows",
                "libs": [f"hdStorm{plugin_suffix}"],
                "libdirs": [plugin_dir],
                "bindirs": [plugin_dir],
                "requires": ["plug", "tf", "trace", "vt", "work", "hd", "hdSt", "opensubdiv::osdcpu", "opensubdiv::osdgpu"],
                "system_libs": []
            },
            "sdrGlslfx": {
                "condition": self.settings.os != "Windows",
                "libs": [f"sdrGlslfx{plugin_suffix}"],
                "libdirs": [plugin_dir],
                "bindirs": [plugin_dir],
                "requires": ["ar", "sdr", "hio"],
                "system_libs": []
            },
            "usdShaders": {
                "condition": self.settings.os != "Windows",
                "libs": [f"usdShaders{plugin_suffix}"],
                "libdirs": [plugin_dir],
                "bindirs": [plugin_dir],
                "requires": ["ar", "sdr", "usdShade"],
                "system_libs": []
            }
        }

    def package_info(self):
        for comp_name, comp_info in self.components_info.items():
            if not comp_info.get("condition", True):
                # It does not fulfill the condition
                continue
            # default library name usd_xxxx
            self.cpp_info.components[comp_name].libs = comp_info.get("libs", [f"usd_{comp_name}"])
            self.cpp_info.components[comp_name].requires = comp_info.get("requires", [])
            if is_apple_os(self):
                self.cpp_info.components[comp_name].frameworks = comp_info.get("frameworks", [])
            if "libdirs" in comp_info:
                self.cpp_info.components[comp_name].libdirs = comp_info["libdirs"]
            if "bindirs" in comp_info:
                self.cpp_info.components[comp_name].bindirs = comp_info["bindirs"]
            elif self.settings.os == "Windows":
                self.cpp_info.components[comp_name].bindirs = ["lib"]
            if "system_libs" in comp_info:
                self.cpp_info.components[comp_name].system_libs = comp_info["system_libs"]
            elif self.settings.os in ["Linux", "FreeBSD"]:
                self.cpp_info.components[comp_name].system_libs = ["m", "pthread", "dl"]
