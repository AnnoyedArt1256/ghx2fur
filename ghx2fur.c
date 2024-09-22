#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stddef.h>
#include <stdint.h>
#include <math.h>

#define NOTE_TRANS (12+3)
#define bankSize 16384

#define max0(x) ((x)<0?0:(x))

FILE* rom, * xm, * data;
long bank;
long offset;
long headerOffset;
int i, j;
int trFix = 0;
char outfile[1000000];
long bankAmt;
int numSongs = 0;
int curSong = 0;
int patRows = 0;
long songTable = 0;
long insTable = 0;
long patTable = 0;
long songInfo[4];
unsigned long seqList[500];
char songNames[50][21];
int totalSeqs;

unsigned static char* romData;
unsigned static char* xmData;
unsigned static char* endData;
long xmLength;

/*Bytes to look for before finding GHX "header" - end of vibrato table*/
const unsigned char magicBytes[8] = { 0x00, 0xFA, 0xF5, 0xF2, 0xF1, 0xF2, 0xF5, 0xFA };
/*"GHX" - start of "header"*/
const unsigned char headerBytes[3] = { 0x47, 0x48, 0x58 };
/*Bytes to check for start of song name list - "SONG"*/
const unsigned char songTitle[4] = { 0x53, 0x4F, 0x4E, 0x47 };

/*Function prototypes*/
unsigned short ReadLE16(unsigned char* Data);
static void Write8B(unsigned char* buffer, unsigned int value);
static void WriteBE32(unsigned char* buffer, unsigned long value);
static void WriteBE24(unsigned char* buffer, unsigned long value);
static void WriteBE16(unsigned char* buffer, unsigned int value);
static void WriteLE16(unsigned char* buffer, unsigned int value);
static void WriteLE24(unsigned char* buffer, unsigned long value);
static void WriteLE32(unsigned char* buffer, unsigned long value);
void song2xm(int songNum, long info[4]);
void getSeqList(unsigned long list[], long offset);
void getSongTitles(char names[50][21]);

/*Convert little-endian pointer to big-endian*/
unsigned short ReadLE16(unsigned char* Data)
{
	return (Data[0] << 0) | (Data[1] << 8);
}

static void Write8B(unsigned char* buffer, unsigned int value)
{
	buffer[0x00] = value;
}

static void WriteBE32(unsigned char* buffer, unsigned long value)
{
	buffer[0x00] = (value & 0xFF000000) >> 24;
	buffer[0x01] = (value & 0x00FF0000) >> 16;
	buffer[0x02] = (value & 0x0000FF00) >> 8;
	buffer[0x03] = (value & 0x000000FF) >> 0;

	return;
}

static void WriteBE24(unsigned char* buffer, unsigned long value)
{
	buffer[0x00] = (value & 0xFF0000) >> 16;
	buffer[0x01] = (value & 0x00FF00) >> 8;
	buffer[0x02] = (value & 0x0000FF) >> 0;

	return;
}

static void WriteBE16(unsigned char* buffer, unsigned int value)
{
	buffer[0x00] = (value & 0xFF00) >> 8;
	buffer[0x01] = (value & 0x00FF) >> 0;

	return;
}

static void WriteLE16(unsigned char* buffer, unsigned int value)
{
	buffer[0x00] = (value & 0x00FF) >> 0;
	buffer[0x01] = (value & 0xFF00) >> 8;

	return;
}

static void WriteLE24(unsigned char* buffer, unsigned long value)
{
	buffer[0x00] = (value & 0x0000FF) >> 0;
	buffer[0x01] = (value & 0x00FF00) >> 8;
	buffer[0x02] = (value & 0xFF0000) >> 16;

	return;
}

static void WriteLE32(unsigned char* buffer, unsigned long value)
{
	buffer[0x00] = (value & 0x000000FF) >> 0;
	buffer[0x01] = (value & 0x0000FF00) >> 8;
	buffer[0x02] = (value & 0x00FF0000) >> 16;
	buffer[0x03] = (value & 0xFF000000) >> 24;

	return;
}

int subSong;

int main(int args, char* argv[])
{
	printf("GHX (Shin'en GBC) to Furnace Module Converter\n");
	printf("Originally based off GHXM by turboboy215\n");
	if (args < 3)
	{
		printf("Usage: ghx2fur <rom> <bank>");
		return -1;
	}
	else
	{
		if ((rom = fopen(argv[1], "rb")) == NULL)
		{
			printf("ERROR: Unable to open file %s!\n", argv[1]);
			exit(1);
		}
		else
		{
			bank = strtol(argv[2], NULL, 16);
			if (bank != 1)
			{
				bankAmt = bankSize;
			}
			else
			{
				bankAmt = 0;
			}
		}
	    subSong = (int)strtol(argv[3], NULL, 16);

		fseek(rom, ((bank - 1) * bankSize), SEEK_SET);
		romData = (unsigned char*)malloc(bankSize);
		fread(romData, 1, bankSize, rom);
		fclose(rom);

		for (i = 0; i < bankSize; i++)
		{
			if (!memcmp(&romData[i], magicBytes, 8))
			{
				for (j = i; j < bankSize; j++)
				{
					if (!memcmp(&romData[j], headerBytes, 3))
					{
						headerOffset = j + bankAmt;
						printf("GHX header found at address 0x%04X!\n", headerOffset);
						break;
					}
				}
				if (headerOffset != NULL)
				{
					numSongs = romData[headerOffset - bankAmt + 3];
					if (numSongs == 0)
					{
						numSongs = 1;
					}
					printf("Number of songs: %i\n", numSongs);
					patRows = romData[headerOffset - bankAmt + 4];
					printf("Rows per pattern: %i\n", patRows);
					patTable = ReadLE16(&romData[headerOffset - bankAmt + 6]);
					printf("Sequence data table: 0x%04X\n", patTable);
					insTable = ReadLE16(&romData[headerOffset - bankAmt + 8]);
					printf("Instrument table: 0x%04X\n", insTable);
                    FILE *temp_file = fopen("ins_table.bin","wb");
                    fputc(insTable&0xff,temp_file);
                    fputc(insTable>>8&0xff,temp_file);
                    fputc(bankAmt&0xff,temp_file);
                    fputc(bankAmt>>8&0xff,temp_file);
					fwrite(romData,1,bankAmt,temp_file);
					fclose(temp_file);
					songTable = ReadLE16(&romData[headerOffset - bankAmt + 10]);
					printf("Song table: 0x%04X\n",songTable);
					getSeqList(seqList, patTable);
					getSongTitles(songNames);

					curSong = subSong;
					i = songTable+curSong*6;
					/*
					for (curSong = 1; curSong <= 1; curSong++)
					{
					*/
						printf("\nSong %i:\n", curSong);
						if (songNames[0][0] != '\0')
						{
							printf("Title: %s\n", songNames[curSong - 1]);
						}
						songInfo[0] = romData[i - bankAmt] + 1;
						printf("Number of patterns: %i\n", songInfo[0]);
						songInfo[1] = ReadLE16(&romData[i - bankAmt + 1]);
						printf("Song data address: 0x%04X\n", songInfo[1]);
						songInfo[2] = romData[i - bankAmt + 3] + 1;
						printf("Loop pattern relative to final pattern: %i\n", songInfo[2]);
						songInfo[3] = ReadLE16(&romData[i - bankAmt + 4]);
						printf("Pattern loop address: 0x%04X\n", songInfo[3]);
						if (songInfo[0] < 128)
						{
							song2xm(curSong, songInfo);
						}
						else
						{
							printf("Invalid song, skipping.\n");
						}

						i += 6;
					//}

				}
				else
				{
					printf("ERROR: Magic bytes not found!\n");
					exit(-1);
				}

			}
		}
		printf("The operation was successfully completed!\n");
	}
}

#define clamp(x, y, z) ((x) > (z) ? (z) : ((x) < (y) ? (y) : (x)))

uint8_t wavs[256][16];

FILE *f;
void write16(uint16_t n) {
    fputc((n>>0)&0xff,f);
    fputc((n>>8)&0xff,f);
}

void write32(uint32_t n) {
    fputc((n>>0)&0xff,f);
    fputc((n>>8)&0xff,f);
    fputc((n>>16)&0xff,f);
    fputc((n>>24)&0xff,f);
}

float freqToNote(float freq) {
    return (12.0*log2(freq/440.0))+68.0;
}

static unsigned char noiseTable[256]={
  0,
  0xf7, 0xf6, 0xf5, 0xf4,
  0xe7, 0xe6, 0xe5, 0xe4,
  0xd7, 0xd6, 0xd5, 0xd4,
  0xc7, 0xc6, 0xc5, 0xc4,
  0xb7, 0xb6, 0xb5, 0xb4,
  0xa7, 0xa6, 0xa5, 0xa4,
  0x97, 0x96, 0x95, 0x94,
  0x87, 0x86, 0x85, 0x84,
  0x77, 0x76, 0x75, 0x74,
  0x67, 0x66, 0x65, 0x64,
  0x57, 0x56, 0x55, 0x54,
  0x47, 0x46, 0x45, 0x44,
  0x37, 0x36, 0x35, 0x34,
  0x27, 0x26, 0x25, 0x24,
  0x17, 0x16, 0x15, 0x14,
  0x07, 0x06, 0x05, 0x04,
  0x03, 0x02, 0x01, 0x00,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
};


uint8_t wav_vol[8] = {15,15,15,15,8,8,4,4};
uint8_t wav_vol2[4] = {15,8,4,0};

void song2xm(int songNum, long info[4]) {
	int curPat = 0;
	long pattern[7];
	unsigned char command[3];
	long curPos = 0;
	int index = 0;
	int curSeq = 0;
	signed int transpose[3] = { 0, 0, 0 };
	long c1Pos = 0;
	long c2Pos = 0;
	long c3Pos = 0;
	long c4Pos = 0;
	long romPos = 0;
	long xmPos = 0;
	int channels = 4;
	int defTicks = 6;
	int bpm = 150;
	long packPos = 0;
	long tempPos = 0;
	int rowsLeft = 0;
	int curChan = 0;
	unsigned char lowNibble = 0;
	unsigned char highNibble = 0;
	long patSize = 0;
	int curNote;

    f = fopen("out.fur","wb");
    FILE *f2 = fopen("ins_use.bin","wb");
    FILE *f3 = fopen("wav_pos.bin","wb");

    fprintf(f, "-Furnace module-");

    write16(144);

    write16(0x00);

    write32(0x20);

    for (int i = 0; i < 8; i++) fputc(0,f);

    fprintf(f, "INFO");
    long o = ftell(f);
    write32(0);

    fputc(0,f);
    fputc(1,f);
    fputc(1,f);
    fputc(1,f);

    write32(0x42700000);

    write16(patRows);
    write16(info[0]);

    fputc(4,f);
    fputc(16,f);

    write16(0);
    write16(64);
    write16(0);

    write32(4*info[0]);

    fputc(0x04,f);
    for (int i = 0; i < 31; i++) fputc(0,f);

    for (int i = 0; i < 32; i++) fputc(0x40,f);
    for (int i = 0; i < 32; i++) fputc(0x00,f);

    for (int i = 0; i < 128; i++) fputc(0x00,f);

    fputc(0,f);
	fputc(0,f);

    write32(0x43DC0000);

    uint8_t flags[20] = {
        0x00, 0x00, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01
    };

    for (int i = 0; i < 20; i++) fputc(flags[i],f);

    long pointer_pos = ftell(f);
    for (int i = 0; i < 4*64; i++) fputc(0,f);

    long pattern_pos = ftell(f);
    for (int i = 0; i < 4*info[0]*4; i++) fputc(0,f);

    for (int i = 0; i < 4; i++) 
        for (int j = 0; j < info[0]; j++) 
            fputc(j,f);

    for (int i = 0; i < 4; i++) fputc(1,f);

    for (int i = 0; i < 4; i++) fputc(3,f);
    for (int i = 0; i < 4; i++) fputc(0,f);

    for (int i = 0; i < 4*2; i++) fputc(0,f);

    fputc(0,f);

    write32(0x3F800000);

    uint8_t flags2[28] = {
        0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01,
        0x00, 0x00, 0x01, 0x00, 0x00, 0x01, 0x04, 
        0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00,
        0x00, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00
    };

    for (int i = 0; i < 28; i++) fputc(flags2[i],f);

    write16(150);
    write16(150);

    fputc(0,f);
    fputc(0,f);

    fputc(0,f);

    for (int i = 0; i < 3; i++) fputc(0,f);

    fprintf(f, "Game Boy");
    fputc(0,f);

    fputc(0,f);
    fputc(0,f);
    fputc(0,f);
    fputc(0,f);
    fputc(0,f);

    write32(0x3F800000);
    write32(0x00000000);
    write32(0x00000000);

    write32(0x00000022);

    write32(0);

    write32(0x010001);

    for (int i = 0; i < 16; i++) write32(0xFFD00000|i);
    for (int i = 0; i < 16; i++) write32(0xFFE00000|i);

    fputc(1,f);

    for (int i = 0; i < 8; i++) fputc(0,f);
    
    fputc(1,f);

    for (int i = 0; i < 16; i++) fputc(6,f);

    fputc(0,f);

    long o2 = ftell(f);
    fseek(f,o,SEEK_SET);
    write32(o2-o);
    fseek(f,0L,SEEK_END);

    o2 = ftell(f);
    fseek(f,pattern_pos,SEEK_SET);
    write32(o2);
    fseek(f,0L,SEEK_END);

    uint8_t wavetable_header[21] = {
        0x57, 0x41, 0x56, 0x45, 0x8D, 0x00, 0x00,
        0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00
    };

    uint16_t wav_len = 0;
	romPos = info[1] - bankAmt;
    for (int i = 0; i < 4*info[0]; i++) {
        fprintf(f, "PATR");
        long s = ftell(f);
        write32(0);

        write16(i&3);
        write16(i>>2);

        write16(0);
        write16(0);

		if ((i&3) == 0) {
			/*The typical pattern format*/
			if (trFix == 0)
			{
				for (index = 0; index < 7; index++)
				{
					pattern[index] = romData[romPos + index];
				}

				/*Get channel information*/
				c1Pos = seqList[pattern[0]];
				transpose[0] = pattern[1];
				c2Pos = seqList[pattern[2]];
				transpose[1] = pattern[3];
				c3Pos = seqList[pattern[4]];
				transpose[2] = pattern[5];
				c4Pos = seqList[pattern[6]];
				romPos += 7;

			}

			/*Alternate pattern format used for Tomb Raider*/
			else
			{
				for (index = 0; index < 11; index++)
				{
					if (index == 0)
					{
						pattern[0] = ReadLE16(&romData[romPos + index]);
					}
					else if (index == 2)
					{
						pattern[1] = romData[romPos + index];
					}
					else if (index == 3)
					{
						pattern[2] = ReadLE16(&romData[romPos + index]);
					}
					else if (index == 5)
					{
						pattern[3] = romData[romPos + index];
					}
					else if (index == 6)
					{
						pattern[4] = ReadLE16(&romData[romPos + index]);
					}
					else if (index == 8)
					{
						pattern[5] = romData[romPos + index];
					}
					else if (index == 9)
					{
						pattern[6] = ReadLE16(&romData[romPos + index]);
					}
				}
				/*Get channel information*/
				c1Pos = pattern[0] - bankAmt;
				transpose[0] = pattern[1];
				c2Pos = pattern[2] - bankAmt;
				transpose[1] = pattern[3];
				c3Pos = pattern[4] - bankAmt;
				transpose[2] = pattern[5];
				c4Pos = pattern[6] - bankAmt;
				romPos += 11;
			}

		}
			for (rowsLeft = patRows; rowsLeft > 0; rowsLeft--)
			{

				int curChan = i&3;
					uint16_t pat_buffer[8] = {0x0000,0x0000,0xFFFF,0xFFFF,0xFFFF,0xFFFF,0xFFFF,0xFFFF};
					if (curChan == 0)
					{
						command[0] = romData[c1Pos];
						command[1] = romData[c1Pos + 1];
						command[2] = romData[c1Pos + 2];
					}
					else if (curChan == 1)
					{
						command[0] = romData[c2Pos];
						command[1] = romData[c2Pos + 1];
						command[2] = romData[c2Pos + 2];
					}
					else if (curChan == 2)
					{
						command[0] = romData[c3Pos];
						command[1] = romData[c3Pos + 1];
						command[2] = romData[c3Pos + 2];
					}
					else if (curChan == 3)
					{
						command[0] = romData[c4Pos];
						command[1] = romData[c4Pos + 1];
						command[2] = romData[c4Pos + 2];
					}
					/*Empty row*/
					if (command[0] == 0)
					{
						pat_buffer[0] = 0;
						pat_buffer[1] = 0;
						if (curChan == 0)
						{
							c1Pos++;
						}
						else if (curChan == 1)
						{
							c2Pos++;
						}
						else if (curChan == 2)
						{
							c3Pos++;
						}
						else if (curChan == 3)
						{
							c4Pos++;
						}
						patSize++;
					}

					/*Pitch slide*/
					else if (command[0] > 0 && command[0] < 0x40)
					{
						int glide_num = (int)command[0]+37;
						pat_buffer[0] = glide_num-NOTE_TRANS;
						pat_buffer[4] = 0x03;
						pat_buffer[5] = 0xFF;
						if (curChan == 0)
						{
							c1Pos++;
						}
						else if (curChan == 1)
						{
							c2Pos++;
						}
						else if (curChan == 2)
						{
							c3Pos++;
						}
						else if (curChan == 3)
						{
							c4Pos++;
						}
						patSize += 3;
					}

					/*Change volume*/
					else if (command[0] == 0x40)
					{
						lowNibble = (command[1] >> 4);
						highNibble = (command[1] & 15);


						if (curChan != 2)
						{
							if (lowNibble == 12)
							{
								lowNibble = 0;
							}
							else if (lowNibble == 8)
							{
								lowNibble = 32;
							}
							else if (lowNibble == 4)
							{
								lowNibble = 48;
							}
							else if (lowNibble == 0)
							{
								lowNibble = 64;
							}
						}
						else
						{
							if (lowNibble == 8)
							{
								lowNibble = 50;
							}
							if (lowNibble == 4)
							{
								lowNibble = 64;
							}
							else if (lowNibble == 3)
							{
								lowNibble = 48;
							}
							else if (lowNibble == 2)
							{
								lowNibble = 32;
							}
							else if (lowNibble == 1)
							{
								lowNibble = 16;
							}
							else if (lowNibble == 0)
							{
								lowNibble = 0;
							}
						}


						if (lowNibble == 0) {
							pat_buffer[0] = 100;
							pat_buffer[1] = 0;
						} else {
                            if (curChan == 2) pat_buffer[3] = wav_vol2[lowNibble>>5&3];
						    else pat_buffer[3] = lowNibble>>4;
                        }

						if (curChan == 0)
						{
							c1Pos+=2;
						}
						else if(curChan == 1)
						{
							c2Pos+=2;
						}
						else if (curChan == 2)
						{
							c3Pos+=2;
						}
						else if (curChan == 3)
						{
							c4Pos+=2;
						}
						patSize += 3;
					}

					/*Standard note + instrument*/
					else if (command[0] > 0x40 && command[0] < 0x80)
					{
						curNote = command[0]-28;
						if (curChan == 0 || curChan == 1 || curChan == 2)
						{
							curNote += (int8_t)transpose[curChan];
						}
						curNote -= NOTE_TRANS;
						pat_buffer[0] = (curNote%12)+1;
						pat_buffer[1] = (curNote-(curNote%12))/12;
						pat_buffer[2] = (command[1]&0x3f)-1;
                        if (curChan == 2) pat_buffer[3] = wav_vol[command[1]>>5];
						else pat_buffer[3] = clamp(0x10/((command[1]>>5)?(command[1]>>5):1),0x00,0x0F);
						pat_buffer[6] = 0x01;
						pat_buffer[7] = 0x00;

                        if ((command[1]&0x3f) != 0) fputc(max0((command[1]&0x3f)-1)|(curChan<<6),f2);
						if (curChan == 0)
						{
							c1Pos+=2;
						}
						else if (curChan == 1)
						{
							c2Pos+=2;
						}
						else if (curChan == 2)
						{
							c3Pos+=2;
						}
						else if (curChan == 3)
						{
							c4Pos+=2;
						}
						patSize += 3;
					}

					/*Tempo (ticks) change*/
					else if (command[0] == 0x80)
					{
						lowNibble = (command[1] >> 4);
						highNibble = (command[1] & 15);


						pat_buffer[4] = 0x0F;
						pat_buffer[5] = lowNibble;
						if (curChan == 0)
						{
							c1Pos+=2;
						}
						else if (curChan == 1)
						{
							c2Pos += 2;
						}
						else if (curChan == 2)
						{
							c3Pos += 2;
						}
						else if (curChan == 3)
						{
							c4Pos += 2;
						}
						patSize += 3;
					}
					
					/*High drum note?*/
					else if (command[0] > 0x80 && command[0] < 0xC0)
					{
						curNote = command[0] - 0x40;
						if (curChan != 3)
						{
							curNote += (int8_t)transpose[curChan];
						}
						curNote -= NOTE_TRANS;
						pat_buffer[0] = (curNote%12)+1;
						pat_buffer[1] = (curNote-(curNote%12))/12;
						pat_buffer[2] = (command[1]&0x3f)-1;
                        if ((command[1]&0x3f) != 0) fputc(max0((command[1]&0x3f)-1)|(curChan<<6),f2);
                        if (curChan == 2) pat_buffer[3] = wav_vol2[command[1]>>5&3];
						else pat_buffer[3] = clamp(0x10/((command[1]>>5)?(command[1]>>5):1),0x00,0x0F);
						if (curChan == 0)
						{
							c1Pos += 2;
						}
						else if (curChan == 1)
						{
							c2Pos += 2;
						}
						else if (curChan == 2)
						{
							c3Pos += 2;
						}
						else if (curChan == 3)
						{
							c4Pos += 2;
						}
						patSize += 3;
					}

					/*Note/instrument + tempo (ticks) change*/
					else if (command[0] >= 0xC0)
					{
						curNote = command[0] - 156;
						lowNibble = (command[2] >> 4);
						highNibble = (command[2] & 15);
						if (curChan != 3)
						{
							curNote += (int8_t)transpose[curChan];
						}
						curNote -= NOTE_TRANS;
						pat_buffer[0] = (curNote%12)+1;
						pat_buffer[1] = (curNote-(curNote%12))/12;
						pat_buffer[2] = (command[1]&0x3f)-1;
                        if (curChan == 2) pat_buffer[3] = wav_vol2[command[1]>>5&3];
						else pat_buffer[3] = clamp(0x10/((command[1]>>5)?(command[1]>>5):1),0x00,0x0F);
						pat_buffer[4] = 0x0F;
						pat_buffer[5] = lowNibble;
                        if ((command[1]&0x3f) != 0) fputc(max0((command[1]&0x3f)-1)|(curChan<<6),f2);

						if (curChan == 0)
						{
							c1Pos += 3;
						}
						else if (curChan == 1)
						{
							c2Pos += 3;
						}
						else if (curChan == 2)
						{
							c3Pos += 3;
						}
						else if (curChan == 3)
						{
							c4Pos += 3;
						}
						patSize += 5;

					}
					for (int byt = 0; byt < 6; byt++) {
						write16(pat_buffer[byt]);	
					}
			}

        fputc(0,f);
        long s2 = ftell(f);
        fseek(f,s,SEEK_SET);
        write32(s2-s);
        fseek(f,pattern_pos+(i*4),SEEK_SET);
        write32(s-4);
        fseek(f,0L,SEEK_END);

	}

    for (int i = 0; i < 64; i++) {
        long s = ftell(f);
        fwrite(wavetable_header,1,21,f);  
        fputc((ftell(f)>>0)&0xff,f3);
        fputc((ftell(f)>>8)&0xff,f3);
        fputc((ftell(f)>>16)&0xff,f3);
        fputc((ftell(f)>>24)&0xff,f3);
        for (int j = 0; j < 16; j++) {
            write32((wavs[i][j]>>4)&0xf);
            write32((wavs[i][j]>>0)&0xf);
        }       
        fseek(f,pointer_pos+(i*4),SEEK_SET);
        write32(s);
        fseek(f,0L,SEEK_END);
    }

    fclose(f);
    fclose(f2);
    fclose(f3);
}


/*Get the pointers to each sequence*/
void getSeqList(unsigned long list[], long offset)
{
	int cnt = 0;
	unsigned long curValue;
	unsigned long curValue2;
	long newOffset = offset;
	long offset2 = offset - bankAmt;

	for (cnt = 0; cnt < 500; cnt++)
	{
		curValue = (ReadLE16(&romData[newOffset - bankAmt])) - bankAmt;
		curValue2 = (ReadLE16(&romData[newOffset - bankAmt]));
		if (curValue2 >= bankAmt && curValue2 < (bankAmt * 2))
		{
			list[cnt] = curValue;
			newOffset += 2;
		}
		else
		{
			totalSeqs = cnt;
			break;
		}
	}
}

/*Get the titles for each song (if present)*/
void getSongTitles(char names[50][21])
{
	long curPos = 0;
	long ptrOffset = 0;
	int k, l = 0;
	for (curPos = 0; curPos < bankSize; curPos++)
	{
		if (!memcmp(&romData[curPos], songTitle, 4))
		{
			ptrOffset = curPos + bankAmt;
			printf("Song table list:  0x%04X!\n", headerOffset);
			break;
		}
	}
	if (ptrOffset != 0)
	{
		curPos += 4;
		for (k = 0; k < numSongs; k++)
		{
			for (l = 0; l < 20; l++)
			{
				songNames[k][l] = romData[curPos + l];
			}
			songNames[k][20] = '\0';
			curPos += 20;
		}
	}
}
