from conans import ConanFile, CMake, tools
import os


class SDL2MixerConan(ConanFile):
    name = "sdl_mixer"
    description = "SDL_mixer is a sample multi-channel audio mixer library"
    topics = ("sdl_mixer", "sdl_mixer", "sdl2", "mixer", "audio", "multimedia", "sound", "music")
    url = "https://github.com/bincrafters/community"
    homepage = "https://www.libsdl.org/projects/SDL_mixer/"
    license = "Zlib"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "cmd": [True, False],
               "wav": [True, False],
               "flac": [True, False],
               "mpg123": [True, False],
               "mad": [True, False],
               "ogg": [True, False],
               "opus": [True, False],
               "mikmod": [True, False],
               "modplug": [True, False],
               "fluidsynth": [True, False],
               "nativemidi": [True, False],
               "tinymidi": [True, False]}

    default_options = {"shared": False,
                       "fPIC": True,
                       "cmd": False,  # needs sys/wait.h
                       "wav": True,
                       "flac": True,
                       "mpg123": True,
                       "mad": True,
                       "ogg": True,
                       "opus": True,
                       "mikmod": True,
                       "modplug": True,
                       "fluidsynth": False, # TODO: add fluidsynth to Conan Center
                       "nativemidi": True,
                       "tinymidi": True}

    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os != "Linux":
            del self.options.tinymidi
        else:
            del self.options.nativemidi

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        self.requires("sdl/2.0.20")
        if self.options.flac:
            self.requires("flac/1.3.3")
        if self.options.mpg123:
            self.requires("mpg123/1.29.3")
        if self.options.mad:
            self.requires("libmad/0.15.1b")
        if self.options.ogg:
            self.requires("ogg/1.3.5")
            self.requires("vorbis/1.3.7")
        if self.options.opus:
            self.requires("opus/1.3.1")
            self.requires("opusfile/0.12")
        if self.options.mikmod:
            self.requires("libmikmod/3.3.11.1")
        if self.options.modplug:
            self.requires("libmodplug/0.8.9.0")
        if self.options.fluidsynth:
            self.requires("fluidsynth/2.2.2")
        if self.settings.os == "Linux":
            if self.options.tinymidi:
                self.requires("tinymidi/cci.20130325")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version],
                  destination=self._source_subfolder, strip_root=True)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake

        self._cmake = CMake(self)
        self._cmake.definitions["CMD"] = self.options.cmd
        self._cmake.definitions["WAV"] = self.options.wav
        self._cmake.definitions["FLAC"] = self.options.flac
        self._cmake.definitions["MP3_MPG123"] = self.options.mpg123
        self._cmake.definitions["MP3_MAD"] = self.options.mad
        self._cmake.definitions["OGG"] = self.options.ogg
        self._cmake.definitions["OPUS"] = self.options.opus
        self._cmake.definitions["MOD_MIKMOD"] = self.options.mikmod
        self._cmake.definitions["MOD_MODPLUG"] = self.options.modplug
        self._cmake.definitions["MID_FLUIDSYNTH"] = self.options.fluidsynth
        if self.settings.os == "Linux":
            self._cmake.definitions["MID_TINYMIDI"] = self.options.tinymidi
            self._cmake.definitions["MID_NATIVE"] = False
        else:
            self._cmake.definitions["MID_TINYMIDI"] = False
            self._cmake.definitions["MID_NATIVE"] = self.options.nativemidi

        self._cmake.definitions["FLAC_DYNAMIC"] = self.options["flac"].shared if self.options.flac else False
        self._cmake.definitions["MP3_MPG123_DYNAMIC"] = self.options["mpg123"].shared if self.options.mpg123 else False
        self._cmake.definitions["OGG_DYNAMIC"] = self.options["ogg"].shared if self.options.ogg else False
        self._cmake.definitions["OPUS_DYNAMIC"] = self.options["opus"].shared if self.options.opus else False
        self._cmake.definitions["MOD_MIKMOD_DYNAMIC"] = self.options["libmikmod"].shared if self.options.mikmod else False
        self._cmake.definitions["MOD_MODPLUG_DYNAMIC"] = self.options["libmodplug"].shared if self.options.modplug else False

        self._cmake.configure(build_folder=self._build_subfolder)

        return self._cmake

    def build(self):
        tools.rmdir(os.path.join(self._source_subfolder, "external"))
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING.txt", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["SDL2_mixer"]

        self.cpp_info.set_property("cmake_file_name", "SDL2_mixer")
        self.cpp_info.set_property("cmake_target_name", "SDL2_mixer::SDL2_mixer")
        self.cpp_info.set_property("pkg_config_name", "SDL2_mixer")

        self.cpp_info.includedirs.append(os.path.join("include", "SDL2"))
        # TODO: Add components in a sane way. SDL2_mixer might be incorrect, as the current dev version uses SDL2::image
        # The current dev version is the first version with official CMake support
        self.cpp_info.names["cmake_find_package"] = "SDL2_mixer"
        self.cpp_info.names["cmake_find_package_multi"] = "SDL2_mixer"
