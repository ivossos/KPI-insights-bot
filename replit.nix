{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.nodejs-18_x
    pkgs.npm-9_x
    pkgs.nodePackages.npm
    pkgs.nodePackages.typescript
    pkgs.chromium
    pkgs.pkg-config
    pkgs.libxslt
    pkgs.libxml2
    pkgs.zlib
    pkgs.libjpeg
    pkgs.libpng
    pkgs.freetype
    pkgs.sqlite
  ];
  
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.glib
      pkgs.xorg.libX11
      pkgs.xorg.libXext
      pkgs.xorg.libXtst
      pkgs.xorg.libXi
      pkgs.xorg.libXrandr
      pkgs.libxslt
      pkgs.libxml2
      pkgs.libjpeg
      pkgs.libpng
      pkgs.freetype
    ];
    
    PYTHONPATH = "${pkgs.python310Full}/lib/python3.10/site-packages";
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = "true";
    PUPPETEER_EXECUTABLE_PATH = "${pkgs.chromium}/bin/chromium";
  };
}