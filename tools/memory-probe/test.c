#define EFIAPI
#include "RmbMemoryProbe.c"
int printf(const char *, ...);
__attribute__((noreturn)) void abort(void);
#define CHECK(x) do { if (!(x)) { printf("FAIL at line %d\n", __LINE__); abort(); } } while (0)

static pci_io gpu;
static loaded_image image_info;
static fs filesystem;
static file root_file, marker_file, output_file;
static u32 configured_top;
static int denied, marker_valid, writes, mmio_reads, closes;
static handle device_handles[1]={(handle)1};
static handle volume_handles[1]={(handle)2};
static int contains(const char *s, const char *needle) {
    for(usize i=0;s[i];i++) {
        usize j=0;while(needle[j]&&s[i+j]==needle[j])j++;
        if(!needle[j])return 1;
    }
    return 0;
}
static status locate(u32 mode,const guid *g,void *unused,usize *n,handle **h) {
    CHECK(mode==2 && (g==&PciGuid||g==&FsGuid));
    *n=1;*h=g==&PciGuid?device_handles:volume_handles;return 0;
}
static status protocol(handle h,const guid *g,void **out) {
    if(g==&PciGuid){*out=&gpu;return 0;}
    if(g==&ImageGuid){*out=&image_info;return 0;}
    if(g==&FsGuid){CHECK(h==(handle)2);*out=&filesystem;return 0;}
    abort();
}
static status config_read(pci_io *p,u32 width,u32 off,usize count,void *data) {
    CHECK(p==&gpu&&width==2&&off==0&&count==1);*(u32 *)data=0x16811002;return 0;
}
static status memory_read(pci_io *p,u32 width,u8 bar,u64 off,usize count,void *data) {
    CHECK(p==&gpu&&width==2&&bar==5&&count==1);mmio_reads++;
    u32 reg=(u32)(off/4);
    switch(reg){
    case 0x295c:case 0x1a8ec:*(u32 *)data=0xf400;break;
    case 0x295d:case 0x1a8ed:*(u32 *)data=configured_top;break;
    case 0x2947:case 0x1a8d7:*(u32 *)data=0x460;break;
    default:abort();}
    return denied ? 0x8000000000000007ULL : 0;
}
static status location(pci_io *p,usize *s,usize *b,usize *d,usize *f) {
    CHECK(p==&gpu);*s=0;*b=3;*d=0;*f=0;return 0;
}
static status release(void *p){CHECK(p==device_handles||p==volume_handles);return 0;}
static status map(usize *size,void *buf,usize *key,usize *stride,u32 *version) {
    CHECK(*size>=48);*size=48;*stride=48;*key=1;*version=1;
    memory_descriptor *d=buf;d->type=0;d->physical=0x460000000ULL;d->pages=0x20000;return 0;
}
static status open_volume(fs *v,file **r){CHECK(v==&filesystem);*r=&root_file;return 0;}
static status open_file(file *r,file **f,const u16 *name,u64 mode,u64 attr) {
    CHECK(r==&root_file&&attr==0);
    if(mode==1)*f=&marker_file;
    else{CHECK(mode==0x8000000000000003ULL&&marker_valid);*f=&output_file;}
    return 0;
}
static status read_file(file *f,usize *n,void *buf){
    CHECK(f==&marker_file&&*n==16);const char *s=marker_valid?"RMB-U352-AUDIT":"OTHER-VOLUME";
    *n=0;while(s[*n]){((char *)buf)[*n]=s[*n];(*n)++;}return 0;
}
static status position(file *f,u64 off){CHECK(f==&output_file&&off==0);return 0;}
static status write_file(file *f,usize *n,const void *data){
    CHECK(f==&output_file&&*n==65536&&data==report);writes++;return 0;
}
static status close_file(file *f){CHECK(f==&root_file||f==&marker_file||f==&output_file);closes++;return 0;}
static status flush(file *f){CHECK(f==&output_file);return 0;}

int main(void) {
    boot_services bs={0};system_table st={0};
    bs.GetMemoryMap=map;bs.HandleProtocol=protocol;bs.LocateHandleBuffer=locate;bs.FreePool=release;
    gpu.Mem.Read=memory_read;gpu.Pci.Read=config_read;gpu.GetLocation=location;
    image_info.device=(handle)2;filesystem.OpenVolume=open_volume;
    root_file.Open=open_file;root_file.Close=close_file;
    marker_file.Read=read_file;marker_file.Close=close_file;
    output_file.Write=write_file;output_file.Close=close_file;output_file.Flush=flush;output_file.SetPosition=position;
    st.BootServices=&bs;
    for(int test=0;test<6;test++) {
        used=0;memset(report,0,sizeof(report));writes=mmio_reads=closes=0;
        configured_top=test==1?0xf47f:0xf41f;denied=test==2;marker_valid=test!=3&&test!=5;
        image_info.device=test>=4?0:(handle)2;
        CHECK(EfiMain((handle)5,&st)==0);CHECK(mmio_reads==6);
        report[sizeof(report)-1]=0;
        if(test==0)CHECK(contains(report,"GCMC_SIZE_MiB=0x0000000000000200"));
        if(test==1)CHECK(contains(report,"GCMC_SIZE_MiB=0x0000000000000800"));
        if(test==2)CHECK(!contains(report,"GCMC_SIZE_MiB="));
        CHECK(writes==(marker_valid?1:0));CHECK(closes==(marker_valid?3:(test==3?4:2)));
    }
    printf("PASS: actual UEFI entry; 512/2048 MiB, read error, USB marker gate, null DeviceHandle, six read-only MMIO accesses.\n");
}
