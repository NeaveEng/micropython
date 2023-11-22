/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2022 Blake W. Felt & Angus Gratton
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#ifndef MICROPY_INCLUDED_SHARED_TINYUSB_MP_USBD_H
#define MICROPY_INCLUDED_SHARED_TINYUSB_MP_USBD_H

#include "py/obj.h"

// Run the TinyUSB device task
void mp_usbd_task(void);

// Schedule a call to mp_usbd_task(), even if no USB interrupt has occurred
void mp_usbd_schedule_task(void);

// Function to be implemented in port code.
// Can write a string up to MICROPY_HW_USB_DESC_STR_MAX characters long, plus terminating byte.
extern void mp_usbd_port_get_serial_number(char *buf);

// Most ports need to write a hexadecimal serial number from a byte array. This
// is a helper function for this. out_str must be long enough to hold a string of total
// length (2 * bytes_len + 1) (including NUL terminator).
void mp_usbd_hex_str(char *out_str, const uint8_t *bytes, size_t bytes_len);

#if MICROPY_HW_ENABLE_USB_RUNTIME_DEVICE
void mp_usbd_deinit(void);
#endif

#endif // MICROPY_INCLUDED_SHARED_TINYUSB_USBD_H
