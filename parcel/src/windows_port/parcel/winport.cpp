//
// Implementations of Linux functions used in the parcel project.
//

#include <winsock2.h>
#include <WS2tcpip.h>

#include "winport.h"

//
// Create and wait on a Waitable Timer.
//

void usleep (__int64 usec)
{
    HANDLE timer;
    LARGE_INTEGER ft;

    //
    // Convert to 100 nanosecond interval, negative value indicates relative time
    //

    ft.QuadPart = -(10 * usec);

    timer = CreateWaitableTimer (NULL, TRUE, NULL);
    SetWaitableTimer (timer, &ft, 0, NULL, NULL, 0);
    WaitForSingleObject (timer, INFINITE);
    CloseHandle (timer);
}

//
// Read from a socket (file descriptor), returning the number of
// bytes read.
//
// Returns count of bytes read or -1 on error.
//

int read (SOCKET fd, char* buffer, int buff_size)
{
    int iResult;

    iResult = recv (fd, buffer, buff_size, 0);

    return iResult;
}

//
// Close a socket.
//
// Returns -1 on error.
//

int close (SOCKET fd)
{
    return closesocket (fd);
}
