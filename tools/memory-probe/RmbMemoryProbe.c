// SPDX-License-Identifier: GPL-2.0-only
// UEFI ABI declarations follow RembrandtGfx/src/HdaSnoop (see ../RembrandtGfx/LICENSE).
// Read the GPU aperture before macOS runs. No PCI/MMIO/NVRAM writes.
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;
typedef u64 usize;
typedef u64 status;
typedef void *handle;
#ifndef EFIAPI
#define EFIAPI __attribute__((ms_abi))
#endif
#define ERROR(x) ((x) >> 63)
typedef struct { u32 a; u16 b, c; u8 d[8]; } guid;
typedef struct { u64 sig; u32 rev, size, crc, reserved; } header;
typedef struct {
    header hdr;
    void *RaiseTPL, *RestoreTPL, *AllocatePages, *FreePages;
    status (EFIAPI *GetMemoryMap)(usize *, void *, usize *, usize *, u32 *);
    void *AllocatePool;
    status (EFIAPI *FreePool)(void *);
    void *CreateEvent, *SetTimer, *WaitForEvent, *SignalEvent, *CloseEvent, *CheckEvent;
    void *InstallProtocolInterface, *ReinstallProtocolInterface, *UninstallProtocolInterface;
    status (EFIAPI *HandleProtocol)(handle, const guid *, void **);
    void *Reserved, *RegisterProtocolNotify, *LocateHandle, *LocateDevicePath, *InstallConfigurationTable;
    void *LoadImage, *StartImage, *Exit, *UnloadImage, *ExitBootServices;
    void *GetNextMonotonicCount, *Stall, *SetWatchdogTimer;
    void *ConnectController, *DisconnectController, *OpenProtocol, *CloseProtocol, *OpenProtocolInformation;
    void *ProtocolsPerHandle;
    status (EFIAPI *LocateHandleBuffer)(u32, const guid *, void *, usize *, handle **);
} boot_services;
typedef struct {
    header hdr; u16 *vendor; u32 revision;
    handle ConsoleInHandle; void *ConIn;
    handle ConsoleOutHandle; void *ConOut;
    handle StandardErrorHandle; void *StdErr;
    void *RuntimeServices;
    boot_services *BootServices;
} system_table;
typedef struct pci_io pci_io;
struct pci_io {
    void *PollMem, *PollIo;
    struct { status (EFIAPI *Read)(pci_io *, u32, u8, u64, usize, void *); void *Write; } Mem;
    struct { void *Read, *Write; } Io;
    struct { status (EFIAPI *Read)(pci_io *, u32, u32, usize, void *); void *Write; } Pci;
    void *CopyMem, *Map, *Unmap, *AllocateBuffer, *FreeBuffer, *Flush;
    status (EFIAPI *GetLocation)(pci_io *, usize *, usize *, usize *, usize *);
};
typedef struct file file;
struct file {
    u64 revision;
    status (EFIAPI *Open)(file *, file **, const u16 *, u64, u64);
    status (EFIAPI *Close)(file *);
    void *Delete;
    status (EFIAPI *Read)(file *, usize *, void *);
    status (EFIAPI *Write)(file *, usize *, const void *);
    void *GetPosition;
    status (EFIAPI *SetPosition)(file *, u64);
    void *GetInfo, *SetInfo;
    status (EFIAPI *Flush)(file *);
};
typedef struct fs fs;
struct fs { u64 revision; status (EFIAPI *OpenVolume)(fs *, file **); };
typedef struct { u32 revision; handle parent; system_table *system; handle device; } loaded_image;
typedef struct { u32 type, pad; u64 physical, virtual_address, pages, attributes; } memory_descriptor;

static const guid PciGuid = {0x4cf5b200,0x68b8,0x4ca5,{0x9e,0xec,0xb2,0x3e,0x3f,0x50,0x02,0x9a}};
static const guid ImageGuid = {0x5b1b31a1,0x9562,0x11d2,{0x8e,0x3f,0x00,0xa0,0xc9,0x69,0x72,0x3b}};
static const guid FsGuid = {0x964e5b22,0x6459,0x11d2,{0x8e,0x39,0x00,0xa0,0xc9,0x69,0x72,0x3b}};
static char report[65536];
static usize used;
static u64 memory_map[8192];

_Static_assert(__builtin_offsetof(boot_services, GetMemoryMap) == 56, "UEFI GetMemoryMap ABI");
_Static_assert(__builtin_offsetof(boot_services, HandleProtocol) == 152, "UEFI HandleProtocol ABI");
_Static_assert(__builtin_offsetof(boot_services, LocateHandleBuffer) == 312, "UEFI LocateHandleBuffer ABI");
_Static_assert(__builtin_offsetof(pci_io, Pci.Read) == 48, "UEFI PCI read ABI");
_Static_assert(__builtin_offsetof(pci_io, GetLocation) == 112, "UEFI PCI location ABI");
_Static_assert(__builtin_offsetof(system_table, BootServices) == 96, "UEFI system table ABI");
_Static_assert(__builtin_offsetof(loaded_image, device) == 24, "UEFI loaded image ABI");

void *memset(void *p, int v, usize n) { u8 *q=p; while(n--) *q++=(u8)v; return p; }
void *memcpy(void *p, const void *s, usize n) { u8 *q=p; const u8 *r=s; while(n--) *q++=*r++; return p; }
static void text(const char *s) { while (*s && used+1<sizeof(report)) report[used++]=*s++; }
static void hex(u64 n) {
    char out[17]; for (int i=15;i>=0;i--) { out[i]="0123456789abcdef"[n&15]; n>>=4; }
    out[16]=0; text("0x"); text(out);
}
static void value(const char *name, u64 n) { text(name); text("="); hex(n); text("\r\n"); }

static void collect_gpu(boot_services *bs) {
    handle *handles=0; usize count=0;
    status s=bs->LocateHandleBuffer(2,&PciGuid,0,&count,&handles);
    value("LocatePciStatus",s); if(ERROR(s)) return;
    for(usize i=0;i<count;i++) {
        pci_io *pci=0; u32 id=0;
        if(ERROR(bs->HandleProtocol(handles[i],&PciGuid,(void **)&pci))) continue;
        if(ERROR(pci->Pci.Read(pci,2,0,1,&id)) || id!=0x16811002) continue;
        value("PCI_ID",id);
        usize seg=0,bus=0,dev=0,fun=0;
        if(!ERROR(pci->GetLocation(pci,&seg,&bus,&dev,&fun))) {
            value("Segment",seg); value("Bus",bus); value("Device",dev); value("Function",fun);
        }
        const u32 registers[]={0x295c,0x295d,0x2947,0x1a8ec,0x1a8ed,0x1a8d7};
        const char *names[]={"GCMC_FB_BASE","GCMC_FB_TOP","GCMC_FB_OFFSET","MMHUB_FB_BASE","MMHUB_FB_TOP","MMHUB_FB_OFFSET"};
        u32 base=0,top=0; int valid=1;
        for(usize j=0;j<6;j++) {
            u32 data=0xffffffff;
            s=pci->Mem.Read(pci,2,5,(u64)registers[j]*4,1,&data);
            value(names[j],data); if(ERROR(s)) value("ReadStatus",s);
            if(j==0) base=data&0xffffff;
            if(j==1) top=data&0xffffff;
            if(j<2 && (ERROR(s)||data==0xffffffff)) valid=0;
        }
        if(valid && top>=base) value("GCMC_SIZE_MiB",((u64)top-base+1)*16);
    }
    bs->FreePool(handles);
}

static void collect_map(boot_services *bs) {
    usize size=sizeof(memory_map),key=0,stride=0; u32 version=0;
    status s=bs->GetMemoryMap(&size,memory_map,&key,&stride,&version);
    value("MemoryMapStatus",s); value("DescriptorSize",stride);
    if(ERROR(s)||stride<sizeof(memory_descriptor)||size>sizeof(memory_map)) return;
    text("MemoryMap: type start pages attributes (hex)\r\n");
    for(usize at=0;at+stride<=size;at+=stride) {
        memory_descriptor *d=(memory_descriptor *)((u8 *)memory_map+at);
        hex(d->type);text(" ");hex(d->physical);text(" ");hex(d->pages);text(" ");hex(d->attributes);text("\r\n");
    }
}

static int save_on_volume(handle device, boot_services *bs) {
    fs *volume=0; file *root=0,*marker=0,*output=0; int saved=0;
    if(ERROR(bs->HandleProtocol(device,&FsGuid,(void **)&volume))) return 0;
    if(ERROR(volume->OpenVolume(volume,&root))) return 0;
    // Only write to the task's USB filesystem, carrying this explicit marker.
    if(!ERROR(root->Open(root,&marker,(const u16 *)L"\\RmbMemoryProbe.tag",1,0))) {
        char contents[16]={0}; usize n=sizeof(contents);
        status read=marker->Read(marker,&n,contents); marker->Close(marker);
        const char expected[]="RMB-U352-AUDIT"; int match=!ERROR(read)&&n>=sizeof(expected)-1;
        for(usize i=0;i<sizeof(expected)-1&&match;i++) if(contents[i]!=expected[i]) match=0;
        if(match && !ERROR(root->Open(root,&output,(const u16 *)L"\\RmbMemoryProbe.txt",0x8000000000000003ULL,0))) {
            // Fixed-size padded output prevents stale suffixes after a shorter subsequent boot.
            for(usize i=used;i<sizeof(report);i++) report[i]='\n';
            usize bytes=sizeof(report);
            if(!ERROR(output->SetPosition(output,0)))
                saved=!ERROR(output->Write(output,&bytes,report))&&bytes==sizeof(report);
            output->Flush(output);output->Close(output);
        }
    }
    root->Close(root);
    return saved;
}

static void save_report(handle image, boot_services *bs) {
    loaded_image *loaded=0;
    if(!ERROR(bs->HandleProtocol(image,&ImageGuid,(void **)&loaded)) && loaded->device
       && save_on_volume(loaded->device,bs)) return;
    // OpenCore 1.0.5 loads drivers from a buffer with no device path: DeviceHandle is null.
    // Locate the explicitly marked USB volume; every unmarked filesystem is read-only here.
    handle *volumes=0; usize count=0;
    if(ERROR(bs->LocateHandleBuffer(2,&FsGuid,0,&count,&volumes))) return;
    for(usize i=0;i<count;i++) if(save_on_volume(volumes[i],bs)) break;
    bs->FreePool(volumes);
}

status EFIAPI EfiMain(handle image, system_table *st) {
    text("RmbMemoryProbe v2: PCI/MMIO/firmware memory map read only\r\n");
    collect_gpu(st->BootServices); collect_map(st->BootServices); save_report(image,st->BootServices);
    return 0;
}
