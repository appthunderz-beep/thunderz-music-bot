{ pkgs }: {
  deps = [
    pkgs.ffmpeg
    pkgs.libopus
    pkgs.python312
    pkgs.python312Packages.pip
  ];
}
