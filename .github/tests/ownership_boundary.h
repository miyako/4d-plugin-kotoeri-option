#pragma once

#import <Carbon/Carbon.h>
#import <Cocoa/Cocoa.h>
#include <cstdlib>

// Forced into every translation unit before the actual plugin is compiled.
static inline CFPropertyListRef ownershipPreference(CFStringRef, CFStringRef)
{
    return CFRetain(CFSTR("synthetic preference"));
}

static inline void ownershipSetPreference(CFStringRef, CFPropertyListRef, CFStringRef)
{
}

static inline Boolean ownershipSynchronize(CFStringRef)
{
    return true;
}

static inline CFURLRef ownershipURL(CFAllocatorRef, CFStringRef, CFURLPathStyle, Boolean)
{
    std::abort();
}

static inline CFStringRef ownershipURLPath(CFURLRef, CFURLPathStyle)
{
    std::abort();
}

static inline void ownershipLog(NSString*, ...)
{
    std::abort();
}

#define CFPreferencesCopyAppValue ownershipPreference
#define CFPreferencesSetAppValue ownershipSetPreference
#define CFPreferencesAppSynchronize ownershipSynchronize
#define CFURLCreateWithFileSystemPath ownershipURL
#define CFURLCopyFileSystemPath ownershipURLPath
#define NSLog ownershipLog
