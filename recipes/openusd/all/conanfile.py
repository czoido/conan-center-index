from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rm, rmdir, apply_conandata_patches, export_conandata_patches
import os

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
        # Require same options as in https://github.com/PixarAnimationStudios/OpenUSD/blob/release/build_scripts/build_usd.py#L1450
        if not self.dependencies["opensubdiv"].options.with_tbb:
            raise ConanInvalidConfiguration('openusd requires -o "opensubdiv/*:with_tbb=True"')
        if not self.dependencies["opensubdiv"].options.with_opengl:
            raise ConanInvalidConfiguration('openusd requires -o "opensubdiv/*:with_opengl=True"')
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
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.extend(["m", "pthread", "dl"])

        kit_framework = "AppKit" if self.settings.os == "Macos" else "UIKit"

        self.cpp_info.components["arch"].libs = ["usd_arch"]

        self.cpp_info.components["tf"].libs = ["usd_tf"]
        self.cpp_info.components["tf"].requires = ["arch", "onetbb::libtbb"]

        self.cpp_info.components["gf"].libs = ["usd_gf"]
        self.cpp_info.components["gf"].requires = ["arch", "tf"]

        self.cpp_info.components["pegtl"].libs = ["usd_pegtl"]
        self.cpp_info.components["pegtl"].requires = ["arch"]

        self.cpp_info.components["js"].libs = ["usd_js"]
        self.cpp_info.components["js"].requires = ["tf"]

        self.cpp_info.components["trace"].libs = ["usd_trace"]
        self.cpp_info.components["trace"].requires = ["arch", "js", "tf", "onetbb::libtbb"]

        self.cpp_info.components["work"].libs = ["usd_work"]
        self.cpp_info.components["work"].requires = ["tf", "trace", "onetbb::libtbb"]

        self.cpp_info.components["plug"].libs = ["usd_plug"]
        self.cpp_info.components["plug"].requires = ["arch", "tf", "js", "trace", "work", "onetbb::libtbb"]

        self.cpp_info.components["vt"].libs = ["usd_vt"]
        self.cpp_info.components["vt"].requires = ["arch", "tf", "gf", "trace", "onetbb::libtbb"]

        self.cpp_info.components["ts"].libs = ["usd_ts"]
        self.cpp_info.components["ts"].requires = ["vt", "gf", "tf"]

        self.cpp_info.components["ar"].libs = ["usd_ar"]
        self.cpp_info.components["ar"].requires = ["arch", "js", "tf", "plug", "vt", "onetbb::libtbb"]

        self.cpp_info.components["kind"].libs = ["usd_kind"]
        self.cpp_info.components["kind"].requires = ["tf", "plug"]

        self.cpp_info.components["sdf"].libs = ["usd_sdf"]
        self.cpp_info.components["sdf"].requires = ["arch", "tf", "gf", "pegtl", "trace", "ts", "vt", "work", "ar", "onetbb::libtbb"]

        self.cpp_info.components["sdr"].libs = ["usd_sdr"]
        self.cpp_info.components["sdr"].requires = ["arch", "plug", "trace", "tf", "vt", "work", "ar", "sdf"]

        self.cpp_info.components["pcp"].libs = ["usd_pcp"]
        self.cpp_info.components["pcp"].requires = ["tf", "trace", "vt", "sdf", "work", "ar", "onetbb::libtbb"]

        self.cpp_info.components["usd"].libs = ["usd_usd"]
        self.cpp_info.components["usd"].requires = ["arch", "kind", "pcp", "sdf", "ar", "plug", "tf", "trace", "ts", "vt", "work", "onetbb::libtbb"]

        self.cpp_info.components["usdGeom"].libs = ["usd_usdGeom"]
        self.cpp_info.components["usdGeom"].requires = ["js", "tf", "plug", "vt", "sdf", "trace", "usd", "work", "onetbb::libtbb"]

        self.cpp_info.components["usdVol"].libs = ["usd_usdVol"]
        self.cpp_info.components["usdVol"].requires = ["tf", "usd", "usdGeom"]

        self.cpp_info.components["usdMedia"].libs = ["usd_usdMedia"]
        self.cpp_info.components["usdMedia"].requires = ["tf", "vt", "sdf", "usd", "usdGeom"]

        self.cpp_info.components["usdShade"].libs = ["usd_usdShade"]
        self.cpp_info.components["usdShade"].requires = ["tf", "vt", "js", "sdf", "sdr", "usd", "usdGeom", "onetbb::libtbb"]

        self.cpp_info.components["usdLux"].libs = ["usd_usdLux"]
        self.cpp_info.components["usdLux"].requires = ["tf", "vt", "sdf", "sdr", "usd", "usdGeom", "usdShade"]

        self.cpp_info.components["usdProc"].libs = ["usd_usdProc"]
        self.cpp_info.components["usdProc"].requires = ["tf", "usd", "usdGeom"]

        self.cpp_info.components["usdRender"].libs = ["usd_usdRender"]
        self.cpp_info.components["usdRender"].requires = ["gf", "tf", "usd", "usdGeom", "usdShade"]

        self.cpp_info.components["usdHydra"].libs = ["usd_usdHydra"]
        self.cpp_info.components["usdHydra"].requires = ["tf", "usd", "usdShade"]

        self.cpp_info.components["usdRi"].libs = ["usd_usdRi"]
        self.cpp_info.components["usdRi"].requires = ["tf", "vt", "sdf", "usd", "usdShade", "usdGeom"]

        self.cpp_info.components["usdSemantics"].libs = ["usd_usdSemantics"]
        self.cpp_info.components["usdSemantics"].requires = ["tf", "vt", "usd"]

        self.cpp_info.components["usdSkel"].libs = ["usd_usdSkel"]
        self.cpp_info.components["usdSkel"].requires = ["arch", "gf", "tf", "trace", "vt", "work", "sdf", "usd", "usdGeom", "onetbb::libtbb"]

        self.cpp_info.components["usdUI"].libs = ["usd_usdUI"]
        self.cpp_info.components["usdUI"].requires = ["tf", "vt", "sdf", "usd"]

        self.cpp_info.components["usdUtils"].libs = ["usd_usdUtils"]
        self.cpp_info.components["usdUtils"].requires = ["arch", "tf", "gf", "sdf", "usd", "usdGeom", "usdShade", "onetbb::libtbb"]

        self.cpp_info.components["usdPhysics"].libs = ["usd_usdPhysics"]
        self.cpp_info.components["usdPhysics"].requires = ["tf", "plug", "vt", "sdf", "trace", "usd", "usdGeom", "usdShade", "work"]

        self.cpp_info.components["vdf"].libs = ["usd_vdf"]
        self.cpp_info.components["vdf"].requires = ["arch", "gf", "tf", "trace", "vt", "work", "onetbb::libtbb"]

        self.cpp_info.components["ef"].libs = ["usd_ef"]
        self.cpp_info.components["ef"].requires = ["vdf", "arch", "tf", "trace", "usd", "work", "onetbb::libtbb"]

        self.cpp_info.components["esf"].libs = ["usd_esf"]
        self.cpp_info.components["esf"].requires = ["arch", "sdf", "tf", "vt", "usd"]

        self.cpp_info.components["esfUsd"].libs = ["usd_esfUsd"]
        self.cpp_info.components["esfUsd"].requires = ["arch", "esf", "tf", "sdf", "usd"]

        self.cpp_info.components["exec"].libs = ["usd_exec"]
        self.cpp_info.components["exec"].requires = ["ef", "esf", "tf", "trace", "ts", "sdf", "usd", "vdf", "vt", "onetbb::libtbb"]

        self.cpp_info.components["execUsd"].libs = ["usd_execUsd"]
        self.cpp_info.components["execUsd"].requires = ["esf", "esfUsd", "exec", "tf", "trace", "sdf", "usd"]

        self.cpp_info.components["execGeom"].libs = ["usd_execGeom"]
        self.cpp_info.components["execGeom"].requires = ["gf", "tf", "execUsd", "usdGeom"]

        self.cpp_info.components["usdValidation"].libs = ["usd_usdValidation"]
        self.cpp_info.components["usdValidation"].requires = ["sdf", "plug", "tf", "gf", "usd", "work"]

        self.cpp_info.components["usdGeomValidators"].libs = ["usd_usdGeomValidators"]
        self.cpp_info.components["usdGeomValidators"].requires = ["tf", "plug", "sdf", "usd", "usdGeom", "usdValidation"]

        self.cpp_info.components["usdPhysicsValidators"].libs = ["usd_usdPhysicsValidators"]
        self.cpp_info.components["usdPhysicsValidators"].requires = ["tf", "plug", "sdf", "usd", "usdGeom", "usdPhysics", "usdValidation"]

        self.cpp_info.components["usdShadeValidators"].libs = ["usd_usdShadeValidators"]
        self.cpp_info.components["usdShadeValidators"].requires = ["tf", "plug", "sdf", "usd", "sdr", "usdShade", "usdValidation"]

        self.cpp_info.components["usdSkelValidators"].libs = ["usd_usdSkelValidators"]
        self.cpp_info.components["usdSkelValidators"].requires = ["tf", "plug", "sdf", "usd", "usdSkel", "usdValidation"]

        self.cpp_info.components["usdUtilsValidators"].libs = ["usd_usdUtilsValidators"]
        self.cpp_info.components["usdUtilsValidators"].requires = ["tf", "plug", "sdf", "usd", "usdUtils", "usdValidation"]

        self.cpp_info.components["garch"].libs = ["usd_garch"]
        self.cpp_info.components["garch"].requires = ["arch", "tf", "opengl::opengl"]
        if is_apple_os(self):
            self.cpp_info.components["garch"].frameworks = ["Foundation", kit_framework]

        self.cpp_info.components["hf"].libs = ["usd_hf"]
        self.cpp_info.components["hf"].requires = ["plug", "tf", "trace"]

        self.cpp_info.components["hio"].libs = ["usd_hio"]
        self.cpp_info.components["hio"].requires = ["arch", "js", "plug", "tf", "vt", "trace", "ar", "hf"]

        self.cpp_info.components["cameraUtil"].libs = ["usd_cameraUtil"]
        self.cpp_info.components["cameraUtil"].requires = ["tf", "gf"]

        self.cpp_info.components["pxOsd"].libs = ["usd_pxOsd"]
        self.cpp_info.components["pxOsd"].requires = ["tf", "gf", "vt", "opensubdiv::osdcpu"]

        self.cpp_info.components["geomUtil"].libs = ["usd_geomUtil"]
        self.cpp_info.components["geomUtil"].requires = ["arch", "gf", "tf", "vt", "pxOsd"]

        self.cpp_info.components["glf"].libs = ["usd_glf"]
        self.cpp_info.components["glf"].requires = ["ar", "arch", "garch", "gf", "hf", "hio", "plug", "tf", "trace", "sdf"]

        self.cpp_info.components["hgi"].libs = ["usd_hgi"]
        self.cpp_info.components["hgi"].requires = ["gf", "plug", "tf", "hio"]

        self.cpp_info.components["hgiGL"].libs = ["usd_hgiGL"]
        self.cpp_info.components["hgiGL"].requires = ["arch", "garch", "hf", "hgi", "tf", "trace"]

        if is_apple_os(self):
            self.cpp_info.components["hgiMetal"].libs = ["usd_hgiMetal"]
            self.cpp_info.components["hgiMetal"].requires = ["arch", "hgi", "tf", "trace"]
            self.cpp_info.components["hgiMetal"].frameworks = ["Foundation", "Metal", kit_framework]

        self.cpp_info.components["hgiInterop"].libs = ["usd_hgiInterop"]
        self.cpp_info.components["hgiInterop"].requires = ["gf", "tf", "hgi", "vt", "garch"]
        if is_apple_os(self):
            self.cpp_info.components["hgiInterop"].frameworks = ["Foundation", "CoreVideo"]
            self.cpp_info.components["hgiInterop"].requires.append("hgiMetal")

        self.cpp_info.components["hd"].libs = ["usd_hd"]
        self.cpp_info.components["hd"].requires = ["plug", "tf", "trace", "vt", "work", "sdf", "cameraUtil", "hf", "pxOsd", "sdr", "onetbb::libtbb"]

        self.cpp_info.components["hdar"].libs = ["usd_hdar"]
        self.cpp_info.components["hdar"].requires = ["hd", "ar"]

        self.cpp_info.components["hdGp"].libs = ["usd_hdGp"]
        self.cpp_info.components["hdGp"].requires = ["hd", "hf", "onetbb::libtbb"]

        self.cpp_info.components["hdsi"].libs = ["usd_hdsi"]
        self.cpp_info.components["hdsi"].requires = ["plug", "tf", "trace", "vt", "work", "sdf", "cameraUtil", "geomUtil", "hf", "hd", "pxOsd", "onetbb::libtbb"]

        self.cpp_info.components["hdSt"].libs = ["usd_hdSt"]
        self.cpp_info.components["hdSt"].requires = ["hio", "garch", "glf", "hd", "hdsi", "hgiGL", "hgiInterop", "sdr", "tf", "trace", "onetbb::libtbb", "opensubdiv::osdcpu", "opensubdiv::osdgpu"]
        if self.options.with_materialx:
            self.cpp_info.components["hdSt"].requires = ["hdMtlx", "materialx::MaterialXGenShader", "materialx::MaterialXRender", "materialx::MaterialXCore", "materialx::MaterialXFormat",
                                                         "materialx::MaterialXGenGlsl", "materialx::MaterialXGenMsl"]
        self.cpp_info.components["hdx"].libs = ["usd_hdx"]
        self.cpp_info.components["hdx"].requires = ["plug", "tf", "vt", "gf", "work", "garch", "glf", "pxOsd", "hd", "hdSt", "hgi", "hgiInterop", "cameraUtil", "sdf"]

        if self.options.with_materialx:
            self.cpp_info.components["usdMtlx"].libs = ["usd_usdMtlx"]
            self.cpp_info.components["usdMtlx"].requires = ["arch", "gf", "sdf", "sdr", "tf", "vt", "usd", "usdGeom", "usdShade", "usdUI", "usdUtils", "materialx::MaterialXCore", "materialx::MaterialXFormat"]

            self.cpp_info.components["hdMtlx"].libs = ["usd_hdMtlx"]
            self.cpp_info.components["hdMtlx"].requires = ["gf", "hd", "sdf", "sdr", "tf", "trace", "usdMtlx", "vt", "materialx::MaterialXCore", "materialx::MaterialXFormat"]

            self.cpp_info.components["usdBakeMtlx"].libs = ["usd_usdBakeMtlx"]
            self.cpp_info.components["usdBakeMtlx"].requires = ["tf", "sdr", "usdMtlx", "usdShade", "hd", "hdMtlx", "usdImaging", "materialx::MaterialXCore", "materialx::MaterialXFormat", "materialx::MaterialXRenderGlsl"]

        self.cpp_info.components["usdImaging"].libs = ["usd_usdImaging"]
        self.cpp_info.components["usdImaging"].requires = ["gf", "tf", "plug", "trace", "vt", "work", "geomUtil", "hd", "hdar", "hio", "pxOsd", "sdf", "usd", "usdGeom", "usdLux", "usdRender", "usdShade", "usdVol", "ar", "onetbb::libtbb"]

        self.cpp_info.components["usdImagingGL"].libs = ["usd_usdImagingGL"]
        self.cpp_info.components["usdImagingGL"].requires = ["gf", "tf", "plug", "trace", "vt", "work", "hio", "garch", "glf", "hd", "hdsi", "hdx", "pxOsd", "sdf", "sdr", "usd", "usdGeom", "usdHydra", "usdShade", "usdImaging", "ar"]

        self.cpp_info.components["usdProcImaging"].libs = ["usd_usdProcImaging"]
        self.cpp_info.components["usdProcImaging"].requires = ["usdImaging", "usdProc"]

        self.cpp_info.components["usdRiPxrImaging"].libs = ["usd_usdRiPxrImaging"]
        self.cpp_info.components["usdRiPxrImaging"].requires = ["gf", "tf", "plug", "trace", "vt", "work", "hd", "pxOsd", "sdf", "usd", "usdGeom", "usdLux", "usdShade", "usdImaging", "usdVol", "ar"]

        self.cpp_info.components["usdSkelImaging"].libs = ["usd_usdSkelImaging"]
        self.cpp_info.components["usdSkelImaging"].requires = ["hio", "hd", "usdImaging", "usdSkel"]

        self.cpp_info.components["usdVolImaging"].libs = ["usd_usdVolImaging"]
        self.cpp_info.components["usdVolImaging"].requires = ["usdImaging"]

        self.cpp_info.components["usdAppUtils"].libs = ["usd_usdAppUtils"]
        self.cpp_info.components["usdAppUtils"].requires = ["garch", "gf", "hio", "sdf", "tf", "usd", "usdGeom", "usdImagingGL"]

        # Plugins
        plugin_suffix = {
            "Windows": "dll",
            "Linux": "so",
            "Macos": "dylib"
        }.get(str(self.settings.os), "so")
        plugin_dir = os.path.join("plugin", "usd")

        self.cpp_info.components["hdStorm"].libs = [f"hdStorm.{plugin_suffix}"]
        self.cpp_info.components["hdStorm"].libdirs = [plugin_dir]
        self.cpp_info.components["hdStorm"].requires = ["plug", "tf", "trace", "vt", "work", "hd", "hdSt", "opensubdiv::osdcpu", "opensubdiv::osdgpu"]

        self.cpp_info.components["hioAvif"].libs = [f"hioAvif.{plugin_suffix}"]
        self.cpp_info.components["hioAvif"].libdirs = [plugin_dir]
        self.cpp_info.components["hioAvif"].requires = ["ar", "arch", "gf", "hio", "tf"]

        if is_apple_os(self):
            self.cpp_info.components["hioImageIO"].libs = [f"hioImageIO.{plugin_suffix}"]
            self.cpp_info.components["hioImageIO"].libdirs = [plugin_dir]
            self.cpp_info.components["hioImageIO"].requires = ["ar", "arch", "gf", "hio", "tf"]
            self.cpp_info.components["hioImageIO"].frameworks = ["Foundation", "ImageIO", "CoreGraphics"]

        if self.options.with_openimageio:
            self.cpp_info.components["hioOiio"].libs = [f"hioOiio.{plugin_suffix}"]
            self.cpp_info.components["hioOiio"].libdirs = [plugin_dir]
            self.cpp_info.components["hioOiio"].requires = ["ar", "arch", "gf", "hio", "tf", "openimageio::openimageio"]

        self.cpp_info.components["sdrGlslfx"].libs = [f"sdrGlslfx.{plugin_suffix}"]
        self.cpp_info.components["sdrGlslfx"].libdirs = [plugin_dir]
        self.cpp_info.components["sdrGlslfx"].requires = ["ar", "sdr", "hio"]

        self.cpp_info.components["usdShaders"].libs = [f"usdShaders.{plugin_suffix}"]
        self.cpp_info.components["usdShaders"].libdirs = [plugin_dir]
        self.cpp_info.components["usdShaders"].requires = ["ar", "sdr", "usdShade"]

