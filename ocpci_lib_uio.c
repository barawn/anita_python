#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/stat.h>
#include <stdbool.h>
#include <libgen.h>

#include "ocpci_lib_uio.h"

#define OCPCI_BAR_SIZE 4096

const char *device_path = "/dev/";
const char *config_path = "/device/config";
const char *resource0_path = "/device/resource0";
const char *resource1_path = "/device/resource1";

int ocpci_lib_uio_irq_init(ocpci_uio_dev_h *dev) {
  int err;

  err = ocpci_lib_uio_irq_unmask(dev);
  if (err) return err;
  
  // enable PCI interrupt propagation across bridge
  dev->bridge->ICR = 0x1;
  return err;
}

int ocpci_lib_uio_irq_wait(ocpci_uio_dev_h *dev) {
  int reenable;
  return (read(dev->irq_fd, &reenable, sizeof(int)) == sizeof(int));
}

int ocpci_lib_uio_irq_unmask(ocpci_uio_dev_h *dev) {
  int err;
  int configfd = dev->cfg_fd;
  unsigned char command_high;

  // unmask PCI interrupts
  err = pread(configfd, &command_high, 1, 5);
  if (err != 1) {
    fprintf(stderr, "ocpci_lib_uio_irq_init: failed to read command register\n");
    return OCPCI_ERR_OPEN;
  }  
  command_high &= ~0x4;
  err = pwrite(configfd, &command_high, 1, 5);
  if (err != 1) {
    fprintf(stderr, "ocpci_lib_uio_irq_init: failed to write command register\n");
    return OCPCI_ERR_OPEN;
  }
  return OCPCI_SUCCESS;
}
  

bool ocpci_uio_is_open(ocpci_uio_dev_h *dev) {
  return dev->valid;
}

unsigned int ocpci_lib_uio_bar1_read(ocpci_uio_dev_h *dev, uint32_t offset) {
  uint32_t mod_offset;
  uint32_t *p;
  uint32_t val;
  if (!dev) return -1;
  if (offset > dev->wb_size) return -1;
  mod_offset = offset >> 2;
  if (offset & 0x3) {
    fprintf(stderr, "ocpci_lib_uio_bar1_read: warning - non-integer aligned read of 0x%8.8x\n", offset);
  }
  p = (uint32_t *) dev->bar1;
  val = *(p + mod_offset);  
  return val;
}

int ocpci_lib_uio_bar1_write(ocpci_uio_dev_h *dev, uint32_t offset, unsigned int value) {
  uint32_t mod_offset;
  uint32_t *p;
  if (!dev) return OCPCI_ERR_INVALID_HANDLE;
  if (offset > dev->wb_size) return OCPCI_ERR_INVALID_REGISTER;
  mod_offset = offset >> 2;
  if (offset & 0x3) {
    fprintf(stderr, "ocpci_lib_uio_bar1_write: error - non-integer aligned write to 0x%8.8x\n - ignoring\n", offset);
    return OCPCI_ERR_UNALIGNED_WRITE;
  }
  p = (uint32_t *) dev->bar1;
  *(p + mod_offset) = value;
  return OCPCI_SUCCESS;
}

int ocpci_lib_uio_open(ocpci_uio_dev_h *dev,
	       const char *path,
	       size_t wb_size) {
  char *tmpstr;
  size_t pathlen;
  char *base;
  
  if (!dev) return OCPCI_ERR_INVALID_HANDLE;
  dev->valid = 0;
  dev->wb_size = wb_size;
  pathlen = strlen(path);
  // Allocate maximum-length temp string.
  tmpstr = malloc(pathlen*sizeof(char) + 
		  strlen(resource1_path)*sizeof(char) + 1);
  if (!tmpstr) return OCPCI_ERR_MEM;

  base = basename((char *) path);
  sprintf(tmpstr, "%s%s", device_path, base);
  dev->irq_fd = open(tmpstr, O_RDWR);
  if (dev->irq_fd < 0) {
    perror("ocpci_open: open irqfd");
    free(tmpstr);
    return OCPCI_ERR_OPEN;
  }
/*
 sprintf(tmpstr, "%s%s", path, config_path);
  dev->cfg_fd = open(tmpstr, O_RDWR | O_SYNC);
  if (dev->cfg_fd < 0) {
    perror("ocpci_open: open cfg");
    free(tmpstr);
    return OCPCI_ERR_OPEN;
  }
*/  
  sprintf(tmpstr, "%s%s", path, resource0_path);
  dev->bar0_fd = open(tmpstr, O_RDWR | O_SYNC);
  if (dev->bar0_fd < 0) {
    perror("ocpci_open: open bar0");
//    close(dev->cfg_fd);
    free(tmpstr);
    return OCPCI_ERR_OPEN;
  }

  sprintf(tmpstr, "%s%s", path, resource1_path);
  dev->bar1_fd = open(tmpstr, O_RDWR | O_SYNC);
  if (dev->bar1_fd < 0) {
    perror("ocpci_open: open bar1");
    close(dev->bar0_fd);
//    close(dev->cfg_fd);
    free(tmpstr);
    return OCPCI_ERR_OPEN;
  }

  // MMAP the bridge control registers.
  dev->bar0 = mmap(NULL, OCPCI_BAR_SIZE, 
		   PROT_READ | PROT_WRITE, MAP_SHARED, dev->bar0_fd, 0);
  if (dev->bar0 == MAP_FAILED) {
    perror("ocpci_open: mmap bar0");
//    close(dev->cfg_fd);
    close(dev->bar0_fd);
    close(dev->bar1_fd);
    free(tmpstr);
    return OCPCI_ERR_OPEN;
  }

  // MMAP the register space.
  dev->bar1 = mmap(NULL, wb_size, 
		   PROT_READ | PROT_WRITE, MAP_SHARED, dev->bar1_fd, 0);
  if (dev->bar1 == MAP_FAILED) {
    perror("ocpci_open: mmap bar1");
    munmap(dev->bar0, OCPCI_BAR_SIZE);    
//    close(dev->cfg_fd);
    close(dev->bar0_fd);
    close(dev->bar1_fd);
    free(tmpstr);
    return OCPCI_ERR_OPEN;
  }
  dev->valid = 1;
  free(tmpstr);
  return OCPCI_SUCCESS;
}

void ocpci_lib_uio_close(ocpci_uio_dev_h *dev) {
  if (!dev) return;
  if (!dev->valid) return;   
  munmap(dev->bar0, OCPCI_BAR_SIZE);
  munmap(dev->bar1, dev->wb_size);
//  close(dev->cfg_fd);
  close(dev->bar0_fd);
  close(dev->bar1_fd);
}
