// 2004.05.28, 2004.10.20, 2005.01.08, 2005.03.25, 2005.04.28, 2005.07.18, 2005.07.28, 2005.09.19, 2007.12.19, 2008.10.15
//****************************************
//**  Copyright  (C)  W.ch  1999-2008   **
//**  Web:  http://www.winchiphead.com  **
//****************************************
//**  DLL for USB interface chip CH341  **
//**  C, VC5.0                          **
//****************************************
//
// USB bus interface chip CH341 parallel port application layer interface library V2.1
// Nanjing Qin Heng Electronics Co., Ltd. author: W.ch 2008.10
// CH341-DLL  V2.1
// Operating environment: Windows 98/ME, Windows 2000/XP
// support USB chip: CH341, CH341A
// USB => Parallel, I2C, SPI, JTAG ...
//

#ifndef		_CH341_DLL_H
#define		_CH341_DLL_H

#include "windows.h"
#include "stdio.h"

#ifdef __cplusplus
extern "C" {
#endif

#define		mOFFSET( s, m )			( (ULONG) & ( ( ( s * ) 0 ) -> m ) )	// Defines the macro that gets the relative offset address of the structure member

#ifndef		max
#define		max( a, b )				( ( ( a ) > ( b ) ) ? ( a ) : ( b ) )	// Larger value
#endif

#ifndef		min
#define		min( a, b )				( ( ( a ) < ( b ) ) ? ( a ) : ( b ) )	// Small value
#endif

#ifdef		ExAllocatePool
#undef		ExAllocatePool						// Remove the memory allocation with TAG
#endif

#ifndef		NTSTATUS
typedef		LONG	NTSTATUS;					// Return status
#endif


typedef	struct	_USB_SETUP_PKT {				// USB controls the data request packet structure for the transmission phase of the transfer
	UCHAR			mUspReqType;				// 00H Request type
	UCHAR			mUspRequest;				// 01H Request code
	union	{
		struct	{
			UCHAR	mUspValueLow;				// 02H Value parameter low byte
			UCHAR	mUspValueHigh;				// 03H Value parameter high byte
		};
		USHORT		mUspValue;					// 02H-03H Value parameter
	};
	union	{
		struct	{
			UCHAR	mUspIndexLow;				// 04H Index parameter low byte
			UCHAR	mUspIndexHigh;				// 05H Index parameter high byte
		};
		USHORT		mUspIndex;					// 04H-05H Indexing parameters
	};
	USHORT			mLength;					// 06H-07H Data length of the data phase
} mUSB_SETUP_PKT, *mPUSB_SETUP_PKT;


#define		mCH341_PACKET_LENGTH	32			// CH341 supports the length of the packet
#define		mCH341_PKT_LEN_SHORT	8			// The length of the short packet supported by CH341


typedef	struct	_WIN32_COMMAND {				// Define the WIN32 command interface structure
	union	{
		ULONG		mFunction;					// Specify the function code or pipe number when entering
		NTSTATUS	mStatus;					// Return to the operating state when output
	};
	ULONG			mLength;					// Access length, return the length of subsequent data
	union	{
		mUSB_SETUP_PKT	mSetupPkt;				// USB controls the data request for the transmission phase of the transfer
		UCHAR			mBuffer[ mCH341_PACKET_LENGTH ];	// Data buffer, length 0 to 255B
	};
} mWIN32_COMMAND, *mPWIN32_COMMAND;


// WIN32 application layer interface command
#define		IOCTL_CH341_COMMAND		( FILE_DEVICE_UNKNOWN << 16 | FILE_ANY_ACCESS << 14 | 0x0f34 << 2 | METHOD_BUFFERED )	// Dedicated interface

#define		mWIN32_COMMAND_HEAD		mOFFSET( mWIN32_COMMAND, mBuffer )	// WIN32 command interface header length

#define		mCH341_MAX_NUMBER		16			// The maximum number of simultaneous CH341 connections

#define		mMAX_BUFFER_LENGTH		0x1000		// The maximum length of the data buffer is 4096

#define		mMAX_COMMAND_LENGTH		( mWIN32_COMMAND_HEAD + mMAX_BUFFER_LENGTH )	// The maximum data length plus the length of the command structure header

#define		mDEFAULT_BUFFER_LEN		0x0400		// Data buffer default length 1024

#define		mDEFAULT_COMMAND_LEN	( mWIN32_COMMAND_HEAD + mDEFAULT_BUFFER_LEN )	// The default data length plus the length of the command structure header


// CH341 endpoint address
#define		mCH341_ENDP_INTER_UP	0x81		// CH341 interrupt data upload endpoint address
#define		mCH341_ENDP_INTER_DOWN	0x01		// CH341 interrupt data download endpoint address
#define		mCH341_ENDP_DATA_UP		0x82		// CH341 The data block uploads the address of the endpoint
#define		mCH341_ENDP_DATA_DOWN	0x02		// CH341 data block to download the endpoint address


// The device layer interface provides the pipe operation command
#define		mPipeDeviceCtrl			0x00000004	// CH341 integrated control pipeline
#define		mPipeInterUp			0x00000005	// CH341 interrupt data upload pipeline
#define		mPipeDataUp				0x00000006	// CH341 data block upload pipeline
#define		mPipeDataDown			0x00000007	// CH341 data block down the pipeline

// Application layer interface function code
#define		mFuncNoOperation		0x00000000	// No operation
#define		mFuncGetVersion			0x00000001	// Get the driver version number
#define		mFuncGetConfig			0x00000002	// Get the USB device configuration descriptor
#define		mFuncSetTimeout			0x00000009	// Set USB communication timeout
#define		mFuncSetExclusive		0x0000000b	// Set exclusive use
#define		mFuncResetDevice		0x0000000c	// Reset the USB device
#define		mFuncResetPipe			0x0000000d	// Reset the USB pipe
#define		mFuncAbortPipe			0x0000000e	// Cancel the data request for the USB pipe

// CH341 parallel port dedicated function code
#define		mFuncSetParaMode		0x0000000f	// Set the port mode
#define		mFuncReadData0			0x00000010	// Read data block 0 from parallel port
#define		mFuncReadData1			0x00000011	// Read data block 1 from parallel port
#define		mFuncWriteData0			0x00000012	// Write data block 0 to parallel port
#define		mFuncWriteData1			0x00000013	// Write data block 1 to parallel port
#define		mFuncWriteRead			0x00000014	// First output and then enter
#define		mFuncBufferMode			0x00000020	// Set the data length in the buffer upload mode and the query buffer
#define		mFuncBufferModeDn		0x00000021	// Sets the data length in the buffer download mode and the query buffer


// USB device standard request code
#define		mUSB_CLR_FEATURE		0x01
#define		mUSB_SET_FEATURE		0x03
#define		mUSB_GET_STATUS			0x00
#define		mUSB_SET_ADDRESS		0x05
#define		mUSB_GET_DESCR			0x06
#define		mUSB_SET_DESCR			0x07
#define		mUSB_GET_CONFIG			0x08
#define		mUSB_SET_CONFIG			0x09
#define		mUSB_GET_INTERF			0x0a
#define		mUSB_SET_INTERF			0x0b
#define		mUSB_SYNC_FRAME			0x0c

// CH341 controls the vendor-specific request type for transmission
#define		mCH341_VENDOR_READ		0xC0		// Through the control of transmission to achieve CH341 vendor-specific read operation
#define		mCH341_VENDOR_WRITE		0x40		// Through the control of transmission to achieve the CH341 vendor dedicated write operation

// CH341 controls the vendor-specific request code for the transfer
#define		mCH341_PARA_INIT		0xB1		// Initialize the port
#define		mCH341_I2C_STATUS		0x52		// Gets the status of the I2C interface
#define		mCH341_I2C_COMMAND		0x53		// Issue a command for the I2C interface

// CH341 parallel port operation command code
#define		mCH341_PARA_CMD_R0		0xAC		// Read data from the parallel port 0, the byte is the length
#define		mCH341_PARA_CMD_R1		0xAD		// Read data from parallel port 1, the secondary byte is the length
#define		mCH341_PARA_CMD_W0		0xA6		// Write data 0 to the parallel port, starting from the second byte for the data stream
#define		mCH341_PARA_CMD_W1		0xA7		// Write data to the parallel port 1, starting from the second byte for the data stream
#define		mCH341_PARA_CMD_STS		0xA0		// Get parallel port state

// CH341A parallel port operation command code
#define		mCH341A_CMD_SET_OUTPUT	0xA1		// Set the parallel port output
#define		mCH341A_CMD_IO_ADDR		0xA2		// MEM with address read / write input, from the sub-byte for the command flow
#define		mCH341A_CMD_PRINT_OUT	0xA3		// PRINT compatible print mode output, starting from the secondary byte for the data stream
#define		mCH341A_CMD_PWM_OUT		0xA4		// The PWM data is output from the command packet, starting from the secondary byte for the data stream
#define		mCH341A_CMD_SHORT_PKT	0xA5		// Short packet, the secondary byte is the true length of the command packet, and the bytes and bytes are the original command packets
#define		mCH341A_CMD_SPI_STREAM	0xA8		// SPI interface command packet, starting from the second byte for the data stream
//#define		mCH341A_CMD_SIO_STREAM	0xA9		// SIO interface command packet, starting from the secondary byte for the data stream
#define		mCH341A_CMD_I2C_STREAM	0xAA		// I2C interface command packet, starting from the secondary byte for the I2C command flow
#define		mCH341A_CMD_UIO_STREAM	0xAB		// UIO interface command packet, starting from the secondary byte for the command flow
#define		mCH341A_CMD_PIO_STREAM	0xAE		// PIO interface command packet, starting from the secondary byte for the data stream

// CH341A controls the vendor-specific request code for the transfer
#define		mCH341A_BUF_CLEAR		0xB2		// Clear unfinished data
#define		mCH341A_I2C_CMD_X		0x54		// Issued a command to the I2C interface, the immediate implementation
#define		mCH341A_DELAY_MS		0x5E		// Specify the time in milliseconds
#define		mCH341A_GET_VER			0x5F		// Get the chip version

#define		mCH341_EPP_IO_MAX		( mCH341_PACKET_LENGTH - 1 )	// CH341 The maximum length of a single read and write data block in EPP / MEM mode
#define		mCH341A_EPP_IO_MAX		0xFF		// CH341A The maximum length of a single read and write data block in EPP / MEM mode

#define		mCH341A_CMD_IO_ADDR_W	0x00		// MEM with address read and write / input and output command flow: write data, bit 6 - bit 0 for the address, the next byte to be written data
#define		mCH341A_CMD_IO_ADDR_R	0x80		// MEM Command line with address read / write output: read data, bit 6 - bit 0 is address, read data return together

#define		mCH341A_CMD_I2C_STM_STA	0x74		// Command flow of the I2C interface: Generates the start bit
#define		mCH341A_CMD_I2C_STM_STO	0x75		// Command flow of the I2C interface: Generates a stop bit
#define		mCH341A_CMD_I2C_STM_OUT	0x80		// I2C interface command flow: output data, bit 5 - bit 0 for the length of the subsequent bytes for the data, 0 length is only sent a byte and return to the response
#define		mCH341A_CMD_I2C_STM_IN	0xC0		// I2C interface command flow: input data, bit 5 - bit 0 for the length, 0 length is only one byte and send no response
#define		mCH341A_CMD_I2C_STM_MAX	( min( 0x3F, mCH341_PACKET_LENGTH ) )	// I2C interface command flow Single command input and output data of the maximum length
#define		mCH341A_CMD_I2C_STM_SET	0x60		// I2C interface command flow: set parameters, bit 2 = I / O number of SPI (0 = single entry, 1 = double entry double), bit 1 bit 0 = I2C speed (00 = low speed, 01 = 10 = fast, 11 = high speed)
#define		mCH341A_CMD_I2C_STM_US	0x40		// Command flow of the I2C interface: Delay in microseconds, bit 3 is the delay value
#define		mCH341A_CMD_I2C_STM_MS	0x50		// I2C interface command flow: in milliseconds for the unit delay, bit 3 - bit 0 for the delay value
#define		mCH341A_CMD_I2C_STM_DLY	0x0F		// I2C interface command flow The maximum value of a single command delay
#define		mCH341A_CMD_I2C_STM_END	0x00		// Command flow of the I2C interface: The command packet ends prematurely

#define		mCH341A_CMD_UIO_STM_IN	0x00		// UIO interface command flow: input data D7-D0
#define		mCH341A_CMD_UIO_STM_DIR	0x40		// UIO interface command flow: set I / O direction D5-D0, bit 5-bit 0 for the direction of data
#define		mCH341A_CMD_UIO_STM_OUT	0x80		// UIO interface command flow: output data D5-D0, bit 5-bit 0 for the data
#define		mCH341A_CMD_UIO_STM_US	0xC0		// UIO interface command flow: microseconds for the unit delay, bit 5 - bit 0 for the delay value
#define		mCH341A_CMD_UIO_STM_END	0x20		// UIO interface command flow: command packet ahead of time


// CH341 parallel port operating mode
#define		mCH341_PARA_MODE_EPP	0x00		// CH341 parallel port operating mode for the EPP way
#define		mCH341_PARA_MODE_EPP17	0x00		// CH341A parallel port operating mode for the EPP mode V1.7
#define		mCH341_PARA_MODE_EPP19	0x01		// CH341A parallel port operating mode for the EPP mode V1.9
#define		mCH341_PARA_MODE_MEM	0x02		// CH341 parallel port working mode MEM mode
#define		mCH341_PARA_MODE_ECP	0x03		// CH341A parallel port operating mode for the ECP way


// I / O direction setting bit definition, direct input of the status signal bit definition, direct output bit data definition
#define		mStateBitERR			0x00000100	// Read only write, ERR # pin input status, 1: high level, 0: low level
#define		mStateBitPEMP			0x00000200	// Read only write, PEMP pin input status, 1: high level, 0: low level
#define		mStateBitINT			0x00000400	// Read only write, INT # pin input status, 1: high level, 0: low level
#define		mStateBitSLCT			0x00000800	// Read only write, SLCT pin input status, 1: high level, 0: low level
#define		mStateBitWAIT			0x00002000	// Read only write, WAIT # pin input status, 1: high level, 0: low level
#define		mStateBitDATAS			0x00004000	// Write-only, DATAS # / READ # pin input status, 1: high, 0: low
#define		mStateBitADDRS			0x00008000	// Write-only, ADDRS # / ADDR / ALE pin input status, 1: high, 0: low
#define		mStateBitRESET			0x00010000	// Write only, RESET # pin input status, 1: high level, 0: low level
#define		mStateBitWRITE			0x00020000	// Write only, WRITE # pin input status, 1: high level, 0: low level
#define		mStateBitSCL			0x00400000	// Read only, SCL pin input status, 1: high level, 0: low level
#define		mStateBitSDA			0x00800000	// Read only, SDA pin input status, 1: high level, 0: low level


#define		MAX_DEVICE_PATH_SIZE	128			// The maximum number of characters for the device name
#define		MAX_DEVICE_ID_SIZE		64			// The maximum number of characters for the device ID


typedef		VOID	( CALLBACK	* mPCH341_INT_ROUTINE ) (  // Interrupt service routine
	ULONG			iStatus );  // Interrupt status data, refer to the following bit description
// Bit 7 - bit 0 corresponds to the D7-D0 pin of CH341
// Bit 8 corresponds to the ERR # pin of CH341, bit 9 corresponds to the PEMP pin of CH341, bit 10 corresponds to the INT # pin of CH341, bit 11 corresponds to the SLCT pin of CH341


HANDLE	WINAPI	CH341OpenDevice(  // Open the CH341 device, return the handle, the error is invalid
	ULONG			iIndex );  // Specify the CH341 device number, 0 corresponds to the first device


VOID	WINAPI	CH341CloseDevice(  // Turn off the CH341 device
	ULONG			iIndex );  // Specify the CH341 device serial number


ULONG	WINAPI	CH341GetVersion( );  // Get the DLL version number and return the version number


ULONG	WINAPI	CH341DriverCommand(  // Directly pass the command to the driver, the error returns 0, otherwise returns the data length
	ULONG			iIndex,  // Specify the CH341 device serial number, V1.6 above DLL can also be a handle after the device is turned on
	mPWIN32_COMMAND	ioCommand );  // Command structure of the pointer
// The program returns the data length after the call, and still returns the command structure. If it is a read operation, the data is returned in the command structure,
// The return data length is 0 when the operation fails, the operation is successful for the length of the entire command structure, such as reading a byte, then return mWIN32_COMMAND_HEAD + 1,
// The command structure is provided before the call, the pipe number or command function code, the length of the access data (optional), the data (optional)
// Command structure after the call, respectively, return: operation status code, the length of the subsequent data (optional),
//   Operation status code is defined by the WINDOWS code, you can refer to NTSTATUS.H,
//   The length of the subsequent data refers to the length of the data returned by the read operation, the data is stored in the subsequent buffer, for the write operation is generally 0


ULONG	WINAPI	CH341GetDrvVersion( );  // Get the driver version number, return the version number, and return 0 if the error occurs


BOOL	WINAPI	CH341ResetDevice(  // Reset the USB device
	ULONG			iIndex );  // Specify the CH341 device serial number


BOOL	WINAPI	CH341GetDeviceDescr(  // Read the device descriptor
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Points to a large enough buffer to hold the descriptor
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341GetConfigDescr(  // Read the configuration descriptor
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Points to a large enough buffer to hold the descriptor
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341SetIntRoutine(  // Set the interrupt service routine
	ULONG			iIndex,  // Specify the CH341 device serial number
	mPCH341_INT_ROUTINE	iIntRoutine );  // Specify the interrupt service routine, NULL to cancel the interrupt service, otherwise call the program when the interrupt


BOOL	WINAPI	CH341ReadInter(  // Read interrupt data
	ULONG			iIndex,  // Specify the CH341 device serial number
	PULONG			iStatus );  // Point to a double word unit, used to save the read interrupt status data, see the next line
// Bit 7 - bit 0 corresponds to the D7-D0 pin of CH341
// Bit 8 corresponds to the ERR # pin of CH341, bit 9 corresponds to the PEMP pin of CH341, bit 10 corresponds to the INT # pin of CH341, bit 11 corresponds to the SLCT pin of CH341


BOOL	WINAPI	CH341AbortInter(  // Abort the interrupt data read operation
	ULONG			iIndex );  // Specify the CH341 device serial number


BOOL	WINAPI	CH341SetParaMode(  // Set the port mode
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iMode );  // Specify the parallel port mode: 0 for EPP mode / EPP mode V1.7, 1 for EPP mode V1.9, 2 for MEM mode


BOOL	WINAPI	CH341InitParallel(  // Reset and initialize the parallel port, RST # output low pulse
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iMode );  // Specify the parallel port mode: 0 for the EPP mode / EPP mode V1.7, 1 for the EPP mode V1.9, 2 for the MEM mode,> = 0x00000100 to keep the current mode


BOOL	WINAPI	CH341ReadData0(  // Read the data block from port 0 #
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Point to a large enough buffer to hold the read data
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341ReadData1(  // Read the data block from port 1 #
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Point to a large enough buffer to hold the read data
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341AbortRead(  // Discard the data block read operation
	ULONG			iIndex );  // Specify the CH341 device serial number


BOOL	WINAPI	CH341WriteData0(  // Write a data block to port 0 #
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			iBuffer,  // Point to a buffer, place the data ready to write
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to write the length of the return to the actual length of the written


BOOL	WINAPI	CH341WriteData1(  // Write a data block to port # 1
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			iBuffer,  // Point to a buffer, place the data ready to write
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to write the length of the return to the actual length of the written


BOOL	WINAPI	CH341AbortWrite(  // Discard the data block write operation
	ULONG			iIndex );  // Specify the CH341 device serial number


BOOL	WINAPI	CH341GetStatus(  // Direct input of data and status via CH341
	ULONG			iIndex,  // Specify the CH341 device serial number
	PULONG			iStatus );  // Point to a double word unit, used to save the status data, refer to the following bit description
// Bit 7 - bit 0 corresponds to the D7-D0 pin of CH341
// Bit 8 corresponds to the ERR # pin of CH341, bit 9 corresponds to the PEMP pin of CH341, bit 10 corresponds to the INT # pin of CH341, bit 11 corresponds to the SLCT pin of CH341, bit 23 corresponds to the SDA pin of CH341
// Bit 13 corresponds to the BUSY / WAIT # pin of CH341, bit 14 corresponds to the AUTOFD # / DATAS # pin of CH341, bit 15 corresponds to the SLCTIN # / ADDRS # pin of CH341


BOOL	WINAPI	CH341ReadI2C(  // Reads one byte of data from the I2C interface
	ULONG			iIndex,  // Specify the CH341 device serial number
	UCHAR			iDevice,  // The lower 7 bits specify the I2C device address
	UCHAR			iAddr,  // Specifies the address of the data unit
	PUCHAR			oByte );  // Point to a byte unit, used to save the read byte data


BOOL	WINAPI	CH341WriteI2C(  // Write one byte of data to the I2C interface
	ULONG			iIndex,  // Specify the CH341 device serial number
	UCHAR			iDevice,  // The lower 7 bits specify the I2C device address
	UCHAR			iAddr,  // Specifies the address of the data unit
	UCHAR			iByte );  // The byte data to be written


BOOL	WINAPI	CH341EppReadData(  // EPP mode read data: WR # = 1, DS # = 0, AS # = 1, D0-D7 = input
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Point to a large enough buffer to hold the read data
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341EppReadAddr(  // EPP mode read address: WR # = 1, DS # = 1, AS # = 0, D0-D7 = input
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Point to a large enough buffer to hold the read address data
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341EppWriteData(  // EPP write data: WR # = 0, DS # = 0, AS # = 1, D0-D7 = output
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			iBuffer,  // Point to a buffer, place the data ready to write
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to write the length of the return to the actual length of the written


BOOL	WINAPI	CH341EppWriteAddr(  // EPP write address: WR # = 0, DS # = 1, AS # = 0, D0-D7 = output
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			iBuffer,  // Point to a buffer, place the address data to be written
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to write the length of the return to the actual length of the written


BOOL	WINAPI	CH341EppSetAddr(  // EPP mode set address: WR # = 0, DS # = 1, AS # = 0, D0-D7 = output
	ULONG			iIndex,  // Specify the CH341 device serial number
	UCHAR			iAddr );  // Specify the EPP address


BOOL	WINAPI	CH341MemReadAddr0(  // MEM mode read address 0: WR # = 1, DS # / RD # = 0, AS # / ADDR = 0, D0-D7 = input
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Points to a large enough buffer to hold the data read from address 0
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341MemReadAddr1(  // MEM mode read address 1: WR # = 1, DS # / RD # = 0, AS # / ADDR = 1, D0-D7 = input
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Points to a large enough buffer to hold the data read from address 1
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341MemWriteAddr0(  // MEM write address 0: WR # = 0, DS # / RD # = 1, AS # / ADDR = 0, D0-D7 = output
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			iBuffer,  // Point to a buffer, place the data ready to write to address 0
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to write the length of the return to the actual length of the written


BOOL	WINAPI	CH341MemWriteAddr1(  // MEM mode write address 1: WR # = 0, DS # / RD # = 1, AS # / ADDR = 1, D0-D7 = output
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			iBuffer,  // Point to a buffer, place the data ready to write to address 1
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to write the length of the return to the actual length of the written


BOOL	WINAPI	CH341SetExclusive(  // Set the exclusive use of the current CH341 device
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iExclusive );  // 0 for the device can be shared, non-0 is exclusive use


BOOL	WINAPI	CH341SetTimeout(  // Set the timeout for USB data read and write
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iWriteTimeout,  // Specifies the timeout time for the USB write data block, in milliseconds mS, 0xFFFFFFFF Specifies not to time out (default)
	ULONG			iReadTimeout );  // Specifies the timeout time for the USB read data block, in milliseconds mS, 0xFFFFFFFF Specifies not to time out (default)


BOOL	WINAPI	CH341ReadData(  // Read the data block
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			oBuffer,  // Point to a large enough buffer to hold the read data
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to read the length of the return to the actual read length


BOOL	WINAPI	CH341WriteData(  // Write the data block
	ULONG			iIndex,  // Specify the CH341 device serial number
	PVOID			iBuffer,  // Point to a buffer, place the data ready to write
	PULONG			ioLength );  // Point to the length of the unit, the input is ready to write the length of the return to the actual length of the written


PVOID	WINAPI	CH341GetDeviceName(  // Returns the buffer pointing to the CH341 device name, and returns NULL if the error occurs
	ULONG			iIndex );  // Specify the CH341 device serial number,0对应第一个设备


ULONG	WINAPI	CH341GetVerIC(  // Get the CH341 chip version, return: 0 = device is invalid, 0x10 = CH341,0x20 = CH341A
	ULONG			iIndex );  // Specify the CH341 device serial number
#define		IC_VER_CH341A		0x20
#define		IC_VER_CH341A3		0x30


BOOL	WINAPI	CH341FlushBuffer(  // Clear the CH341 buffer
	ULONG			iIndex );  // Specify the CH341 device serial number


BOOL	WINAPI	CH341WriteRead(  // Execute the data flow command, first output and then enter
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iWriteLength,  // Write length, ready to write the length
	PVOID			iWriteBuffer,  // Point to a buffer, place the data ready to write
	ULONG			iReadStep,  // Ready to read the length of a single block, ready to read the total length of (iReadStep * iReadTimes)
	ULONG			iReadTimes,  // Ready to read the number of times
	PULONG			oReadLength,  // Point to the length of the unit, after returning to the actual read length
	PVOID			oReadBuffer );  // Point to a large enough buffer to hold the read data


BOOL	WINAPI	CH341SetStream(  // Set the serial flow mode
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iMode );  // Specify the mode, see descending
// Bit 1 bit 0: I2C interface speed / SCL frequency, 00 = low speed / 20KHz, 01 = standard / 100KHz (default), 10 = fast / 400KHz, 11 = high speed / 750KHz
// Bit 2: SPI I / O count / IO pin, 0 = single entry (D3 clock / D5 out / D7 in) (default), 1 = double entry double (D3 clock / D5 out D4 out / D7 into D6 into)
// Bit 7: bit order in SPI byte, 0 = low first, 1 = high first
// Other reservations must be 0


BOOL	WINAPI	CH341SetDelaymS(  // Set the hardware asynchronous delay, call back quickly, and delay the specified number of milliseconds before the next stream operation
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iDelay );  // Specifies the number of milliseconds for the delay


BOOL	WINAPI	CH341StreamI2C(  // Processing I2C data stream, 2-wire interface, the clock line for the SCL pin, the data line for the SDA pin (quasi-bidirectional I / O), the speed of about 56K bytes
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iWriteLength,  // Ready to write the number of data bytes
	PVOID			iWriteBuffer,  // Point to a buffer, place the data to be written, the first byte is usually the I2C device address and read and write direction bits
	ULONG			iReadLength,  // Ready to read the number of data bytes
	PVOID			oReadBuffer );  // Point to a buffer, return after reading the data


typedef	enum	_EEPROM_TYPE {					// EEPROM model
	ID_24C01,
	ID_24C02,
	ID_24C04,
	ID_24C08,
	ID_24C16,
	ID_24C32,
	ID_24C64,
	ID_24C128,
	ID_24C256,
	ID_24C512,
	ID_24C1024,
	ID_24C2048,
	ID_24C4096
} EEPROM_TYPE;


BOOL	WINAPI	CH341ReadEEPROM(  // Read the data block from the EEPROM at a speed of about 56K bytes
	ULONG			iIndex,  // Specify the CH341 device serial number
	EEPROM_TYPE		iEepromID,  // Specify the EEPROM model
	ULONG			iAddr,  // Specifies the address of the data unit
	ULONG			iLength,  // Ready to read the number of data bytes
	PUCHAR			oBuffer );  // Point to a buffer, return after reading the data


BOOL	WINAPI	CH341WriteEEPROM(  // Write a data block to the EEPROM
	ULONG			iIndex,  // Specify the CH341 device serial number
	EEPROM_TYPE		iEepromID,  // Specify the EEPROM model
	ULONG			iAddr,  // Specifies the address of the data unit
	ULONG			iLength,  // Ready to write the number of data bytes
	PUCHAR			iBuffer );  // Point to a buffer, place the data ready to write


BOOL	WINAPI	CH341GetInput(  // By CH341 direct input data and status, the efficiency is higher than CH341GetStatus
	ULONG			iIndex,  // Specify the CH341 device serial number
	PULONG			iStatus );  // Point to a double word unit, used to save the status data, refer to the following bit description
// Bit 7 - bit 0 corresponds to the D7-D0 pin of CH341
// Bit 8 corresponds to the ERR # pin of CH341, bit 9 corresponds to the PEMP pin of CH341, bit 10 corresponds to INT # pin of CH341, bit 11 corresponds to the SLCT pin of CH341, bit 23 corresponds to the SDA pin of CH341
// Bit 13 corresponds to the BUSY / WAIT # pin of CH341, bit 14 corresponds to the AUTOFD # / DATAS # pin of CH341, bit 15 corresponds to the SLCTIN # / ADDRS # pin of CH341


BOOL	WINAPI	CH341SetOutput(  // Set the I / O direction of CH341 and output data directly via CH341
/* ***** Use this API with caution to prevent the I / O direction from changing the input pin into an output pin that causes a short circuit between the output pins and other output pins ***** */
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iEnable,  // Data valid flag, refer to the following bit description
// Bit 0 is 1 to indicate that bit 15 of bit iSetDataOut is valid, otherwise it is ignored
// Bit 1 is 1 to indicate that bit 15 of bit iSetDirOut is valid, otherwise it is ignored
// Bit 2 is 1 to indicate that the 7-bit 0 of iSetDataOut is valid, otherwise it is ignored
// Bit 3 is 1 to indicate that bit 7 of bit iSetDirOut is valid, otherwise it is ignored
// Bit 4 is 1 to indicate that bit 13 - bit 16 of iSetDataOut is valid, otherwise it is ignored
	ULONG			iSetDirOut,  // Set the I / O direction, a clear 0 is the corresponding pin for the input, a position of the corresponding pin for the output, parallel port default value of 0x000FC000, refer to the following bit description
	ULONG			iSetDataOut );  // Output data, if the I / O direction for the output, then a bit cleared to 0 when the corresponding pin output low, a position corresponding to the pin output high, refer to the following bit description
// Bit 7 - bit 0 corresponds to the D7-D0 pin of CH341
// Bit 8 corresponds to the ERR # pin of CH341, bit 9 corresponds to the PEMP pin of CH341, bit 10 corresponds to the INT # pin of CH341, bit 11 corresponds to the SLCT pin of CH341
// Bit 13 corresponds to the WAIT # pin of CH341, bit 14 corresponds to the DATAS # / READ # pin of CH341, bit 15 corresponds to the ADDRS # / ADDR / ALE pin of CH341
// The following pins can only be output without considering the I / O direction: Bit 16 corresponds to the RESET # pin of CH341, bit 17 corresponds to CH131's WRITE # pin, bit 18 corresponds to CH341's SCL pin, bit 29 corresponds to CH341 SDA foot


BOOL	WINAPI	CH341Set_D5_D0(  // Set the I / O direction of the D5-D0 pin of CH341 and output data directly through the D5-D0 pin of CH341, which is higher than CH341SetOutput
/* ***** Use this API with caution to prevent the I / O direction from changing the input pin into an output pin that causes a short circuit between the output pins and other output pins ***** */
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iSetDirOut,  // Set the D5-D0 pin I / O direction, a clear 0 is the corresponding pin for the input, a position of the corresponding pin for the output, parallel port mode default value of 0x00 all input
	ULONG			iSetDataOut );  // Set the output data of each pin of D5-D0. If the I / O direction is output, the corresponding pin output is low when a bit is cleared to 0, and the pin output is high when a bit is set
// The bits 5 to 0 of the above data correspond to the D5-D0 pin of CH341, respectively


BOOL	WINAPI	CH341StreamSPI3(  // The API has expired and should not be used
	ULONG			iIndex,
	ULONG			iChipSelect,
	ULONG			iLength,
	PVOID			ioBuffer );


BOOL	WINAPI	CH341StreamSPI4(  // Processing the SPI data stream, 4-wire interface, the clock line for the DCK / D3 pin, the output data line DOUT / D5 pin, the input data line for the DIN / D7 pin, chip line for the D0 / D1 / D2, the speed of about 68K bytes
/* SPI Timing: The DCK / D3 pin is clocked and defaults to the low level. The DOUT / D5 pin is output during the low period before the rising edge of the clock. The DIN / D7 pin is at a high level before the falling edge of the clock enter */
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iChipSelect,  // Chip select control, bit 7 is 0 is ignored chip select control, bit 7 is 1 parameter is valid: bit 1 bit 0 is 00/01/10 select D0 / D1 / D2 pin as low active chip select
	ULONG			iLength,  // The number of bytes of data to be transferred
	PVOID			ioBuffer );  // Point to a buffer, place the data to be written from DOUT, and return the data read from DIN


BOOL	WINAPI	CH341StreamSPI5(  // The output data lines are DOUT / D5 and DOUT2 / D4 pins. The input data lines are DIN / D7 and DIN2 / D6. The chip line is D0 / D1 / D2, the speed of about 30K bytes * 2
/* SPI Timing: The DCK / D3 pin is clocked and defaults to the low level. The DOUT / D5 and DOUT2 / D4 pins are output during the low level before the rising edge of the clock. The DIN / D7 and DIN2 / D6 pins are clocked The falling edge of the previous high period is entered */
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iChipSelect,  // Chip select control, bit 7 is 0 is ignored chip select control, bit 7 is 1 parameter is valid: bit 1 bit 0 is 00/01/10 select D0 / D1 / D2 pin as low active chip select
	ULONG			iLength,  // The number of bytes of data to be transferred
	PVOID			ioBuffer,  // Point to a buffer, place the data to be written from DOUT, and return the data read from DIN
	PVOID			ioBuffer2 );  // Point to the second buffer, place the data to be written from DOUT2, and return the data read from DIN2


BOOL	WINAPI	CH341BitStreamSPI(  // Processing the SPI bit data stream, 4 line / 5 line interface, the clock line for the DCK / D3 pin, the output data line DOUT / DOUT2 pin, the input data line for the DIN / DIN2 pin, chip select line D0 / D1 / D2, the speed of about 8K bit * 2
	ULONG			iIndex,  // Specify the CH341 device serial number
	ULONG			iLength,  // Ready to transfer the number of data bits, up to 896 at a time, it is recommended not to exceed 256
	PVOID			ioBuffer );  // Point to a buffer, place the data to be written from DOUT / DOUT2 / D2-D0, and return the data read from DIN / DIN2
/* SPI Timing: The DCK / D3 pin is clocked and defaults to the low level. The DOUT / D5 and DOUT2 / D4 pins are output during the low level before the rising edge of the clock. The DIN / D7 and DIN2 / D6 pins are clocked The falling edge of the previous high period is entered */
/* A bit in the ioBuffer is 8 bits corresponding to the D7-D0 pin, bit 5 is output to DOUT, bit 4 is output to DOUT2, bit 2-bit 0 is output to D2-D0, bit 7 is input from DIN, bit 6 from DIN2 Input, bit 3 data ignored */
/* Before calling the API, you should call CH341Set_D5_D0 to set the I / O direction of the D5-D0 pin of CH341 and set the default level of the pin */


BOOL	WINAPI	CH341SetBufUpload(  // Set the internal buffer upload mode
	ULONG			iIndex,  // Specify the CH341 device serial number, 0 corresponds to the first device
	ULONG			iEnableOrClear );  // 0 for internal buffer upload mode, use direct upload, non-0 to enable internal buffer upload mode and clear existing data in buffer
// If the internal buffer upload mode is enabled, the CH341 driver creates a thread that automatically receives USB upload data into the internal buffer and clears the existing data in the buffer. When the application calls CH341ReadData, it immediately returns the existing data in the buffer


LONG	WINAPI	CH341QueryBufUpload(  // Query the number of existing packets in the internal upload buffer, the number of packets returned successfully, and the error returns -1
	ULONG			iIndex );  // Specify the CH341 device serial number, 0 corresponds to the first device


BOOL	WINAPI	CH341SetBufDownload(  // Set the internal buffer download mode
	ULONG			iIndex,  // Specify the CH341 device serial number, 0 corresponds to the first device
	ULONG			iEnableOrClear );  // 0 is disabled for internal buffer download mode, using direct download, non-0 to enable the internal buffer download mode and clear the existing data in the buffer
// If the internal buffer download mode is enabled, then when the application calls CH341WriteData, it will simply put the USB download data into the internal buffer and return immediately, and the thread created by the CH341 driver will be sent automatically


LONG	WINAPI	CH341QueryBufDownload(  // Query the number of remaining packets in the internal drop buffer (not yet sent), the number of packets returned successfully, the error returns -1
	ULONG			iIndex );  // Specify the CH341 device serial number, 0 corresponds to the first device


BOOL	WINAPI	CH341ResetInter(  // Reset interrupt data read operation
	ULONG			iIndex );  // Specify the CH341 device serial number


BOOL	WINAPI	CH341ResetRead(  // Reset the data block read operation
	ULONG			iIndex );  // Specify the CH341 device serial number


BOOL	WINAPI	CH341ResetWrite(  // Reset the data block write operation
	ULONG			iIndex );  // Specify the CH341 device serial number


typedef		VOID	( CALLBACK	* mPCH341_NOTIFY_ROUTINE ) (  // Device event notification callback procedure
	ULONG			iEventStatus );  // Device events and current status (defined in the following): 0 = Device pull event, 3 = Device insert event

#define		CH341_DEVICE_ARRIVAL		3		// Device insertion event has been inserted
#define		CH341_DEVICE_REMOVE_PEND	1		// The device will be pulled out
#define		CH341_DEVICE_REMOVE			0		// The device pulls out and has been pulled out


BOOL	WINAPI	CH341SetDeviceNotify(  // Set the device event notification program
	ULONG					iIndex,  // Specify the CH341 device serial number, 0 corresponds to the first device
	PCHAR					iDeviceID,  // Optional parameter, point to the string, specify the ID of the device being monitored, the string ends with \ 0
	mPCH341_NOTIFY_ROUTINE	iNotifyRoutine );  // Specify the device event callback program, NULL to cancel the event notification, or call the event when an event is detected


BOOL	WINAPI	CH341SetupSerial(  // Set the CH341 serial port features, the API can only be used in the serial port of the CH341 chip
	ULONG					iIndex,  // Specify the CH341 device serial number, 0 corresponds to the first device
	ULONG					iParityMode,  // Specify the data verification mode of the CH341 serial port: NOPARITY / ODDPARITY / EVENPARITY / MARKPARITY / SPACEPARITY
	ULONG					iBaudRate );  // Specifies the communication baud rate value of the CH341 serial port, which can be any value between 50 and 3000000

/*  The following API can be used to work in the serial port CH341 chip, in addition to the API can only be used for parallel port CH341 chip
	CH341OpenDevice
	CH341CloseDevice
	CH341SetupSerial
	CH341ReadData
	CH341WriteData
	CH341SetBufUpload
	CH341QueryBufUpload
	CH341SetBufDownload
	CH341QueryBufDownload
	CH341SetDeviceNotify
	CH341GetStatus
//  The above is the main API, the following is the secondary API
	CH341GetVersion
	CH341DriverCommand
	CH341GetDrvVersion
	CH341ResetDevice
	CH341GetDeviceDescr
	CH341GetConfigDescr
	CH341SetIntRoutine
	CH341ReadInter
	CH341AbortInter
	CH341AbortRead
	CH341AbortWrite
	CH341ReadI2C
	CH341WriteI2C
	CH341SetExclusive
	CH341SetTimeout
	CH341GetDeviceName
	CH341GetVerIC
	CH341FlushBuffer
	CH341WriteRead
	CH341ResetInter
	CH341ResetRead
	CH341ResetWrite
*/
HANDLE	WINAPI	CH341OpenDeviceEx(   // Open the CH341 device, return the handle, the error is invalid
    ULONG			iIndex );        // Specify the CH341 device serial number, 0 corresponds to the first device inserted, 1 corresponds to the second device inserted, in order to save equipment equipment serial number resources, after the use of equipment to shut down

VOID	WINAPI	CH341CloseDeviceEx(  // Turn off the CH341 device
	ULONG			iIndex );        // Specify the CH341 device serial number

PCHAR	WINAPI	CH341GetDeviceNameEx(   // Returns the buffer pointing to the CH341 device name, and returns NULL if the error occurs
	ULONG			iIndex );           // Specify the CH341 device serial number, 0 corresponds to the first device

BOOL	WINAPI	CH341SetDeviceNotifyEx(       // Set the device event notification program
	ULONG					iIndex,           // Specify the CH341 device serial number, 0 corresponds to the first device
	PCHAR					iDeviceID,        // Optional parameter, point to the string, specify the ID of the device being monitored, the string ends with \ 0
	mPCH341_NOTIFY_ROUTINE	iNotifyRoutine ); // Specify the device event callback program, NULL to cancel the event notification, or call the event when an event is detected


#ifdef __cplusplus
}
#endif

#endif		// _CH341_DLL_H
