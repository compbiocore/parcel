#pragma once

//
// Windows implementation of Linux functions used in the parcel project.
//

//
// usleep implementation for Windows.  Sleeps for usec microseconds.
//

void usleep (__int64 usec);

//
// Read from a socket (file descriptor), returning the number of
// bytes read.
//
// Returns count of bytes read or -1 on error.
//

int read (int fd, char* buffer, int buff_size);

//
// Close a socket.
//
// Returns -1 on error.
//

int close (int fd);
