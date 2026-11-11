# Third-party notices

This local RTL8852B Ready adaptation is based on
[tanner02/RealtekBluetoothCompat](https://github.com/tanner02/RealtekBluetoothCompat),
commit `ef5294418e3c4c228b72c7309ba13448e382fcec`. The source is distributed under
GPL version 2 only; see [LICENSE](LICENSE). It is an independent local branch,
not an upstream support declaration.

The code-validation routing approach is adapted from `BlueToolFixup.cpp`,
created by Dhinak G (2021) in acidanthera/BrcmPatchRAM. The local source used
commit `65389020769837e92e9fb939bac34bd9a3e25bb2`. That project's GPL version 2
license is retained as [LICENSE](LICENSE).

Lilu startup code and headers are used from commit
`e4748cc081bf060302c7d3c44a643ce1d11b7e1d`. Lilu is copyright (c) 2016–2018
vit9696 and contributors, under BSD-3-Clause. Its license is reproduced in
[licenses/Lilu-LICENSE.txt](licenses/Lilu-LICENSE.txt). Preserve it when
distributing a work incorporating Lilu code.

MacKernelSDK is used from commit `3f750085caa17ec3a7880f11c11bf4f48cd6a164`.
Its files retain their respective Apple and upstream notices. Neither build
dependency's source tree is bundled here; the fixed Git checkouts are supplied
explicitly to `build.py`.

The XNU `vn_getcdhash(vnode_t, off_t, unsigned char *, uint8_t *)` signature was
checked against Apple's
[xnu-11417.140.69 source](https://github.com/apple-oss-distributions/xnu/blob/xnu-11417.140.69/bsd/vfs/vfs_subr.c).

Apple executables are not included. Full original-page fixtures and compiled
kexts containing them are generated locally and excluded from publication.
The project's GPL notice does not relicense Apple code in those generated
files. Published hashes, patch offsets and compatibility logic describe this
build-specific mechanism.
