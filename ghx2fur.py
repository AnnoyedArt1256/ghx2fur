import sys, math
bank_size = 16384
NOTE_TRANS = 12+3
trFix = 0

print(sys.argv)

# end of vibrato table
magic_bytes = [0x00, 0xFA, 0xF5, 0xF2, 0xF1, 0xF2, 0xF5, 0xFA]

# "GHX" (start of header)
header_bytes = [0x47, 0x48, 0x58]

gb = open(sys.argv[1],"rb")
bank = int(sys.argv[2])
gb.seek(bank*bank_size)
rom_data = list(gb.read(bank_size))
rom_data += [0]*(bank_size-len(rom_data))
gb.close()

seq_list = []

def get_seq_list(pat_table):
    cnt = 0
    offset = pat_table%bank_size
    arr = []
    for i in range(256):
        val = rom_data[offset]|(rom_data[offset + 1]<<8)
        arr.append(val%bank_size)
        offset += 2
    return arr

f = 0

def fprintf(f,w):
    f.write(w.encode("ascii"))

def write8(w):
    f.write(bytearray([int(w)&0xff]))


def write16(w):
    f.write(bytearray([int(w)&0xff,int(w)>>8&0xff]))

def write32(w):
    f.write(bytearray([int(w)&0xff,int(w)>>8&0xff,int(w)>>16&0xff,int(w)>>24&0xff]))

def conv_int8(n):
    if n >= 0x80:
        return n-0x100
    else:
        return n

def do_vol(v):
    return [0xf,0x8,0x4,0x2][v]

wav_vol = [15,4,8,15]

FUR_noise = [
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
  0x03, 0x02, 0x01, 0x00
]

GHX_noise = [
0x90, 0x57, 0x63, 0x63, 0x55, 0x55, 0x80, 0x47,
0x53, 0x53, 0x45, 0x45, 0x70, 0x37, 0x43, 0x43,
0x35, 0x35, 0x60, 0x27, 0x33, 0x33, 0x25, 0x25,
0x50, 0x17, 0x23, 0x23, 0x15, 0x15, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0xFF,
0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00,
]

vibrato_table = [
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
  0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x01, 0x01,
  0x02, 0x01, 0x01, 0x00, 0x00, 0xff, 0xfe, 0xfe, 0xfe, 0xfe, 0xfe, 0xff,
  0x00, 0x01, 0x02, 0x02, 0x03, 0x02, 0x02, 0x01, 0x00, 0xfe, 0xfd, 0xfd,
  0xfd, 0xfd, 0xfd, 0xfe, 0x00, 0x01, 0x02, 0x03, 0x04, 0x03, 0x02, 0x01,
  0x00, 0xfe, 0xfd, 0xfc, 0xfc, 0xfc, 0xfd, 0xfe, 0x00, 0x01, 0x03, 0x04,
  0x05, 0x04, 0x03, 0x01, 0x00, 0xfe, 0xfc, 0xfb, 0xfb, 0xfb, 0xfc, 0xfe,
  0x00, 0x02, 0x04, 0x05, 0x06, 0x05, 0x04, 0x02, 0x00, 0xfd, 0xfb, 0xfa,
  0xfa, 0xfa, 0xfb, 0xfd, 0x00, 0x02, 0x04, 0x06, 0x07, 0x06, 0x04, 0x02,
  0x00, 0xfd, 0xfb, 0xf9, 0xf9, 0xf9, 0xfb, 0xfd, 0x00, 0x03, 0x05, 0x07,
  0x08, 0x07, 0x05, 0x03, 0x00, 0xfc, 0xfa, 0xf8, 0xf8, 0xf8, 0xfa, 0xfc,
  0x00, 0x03, 0x06, 0x08, 0x09, 0x08, 0x06, 0x03, 0x00, 0xfc, 0xf9, 0xf7,
  0xf7, 0xf7, 0xf9, 0xfc, 0x00, 0x03, 0x07, 0x09, 0x0a, 0x09, 0x07, 0x03,
  0x00, 0xfc, 0xf8, 0xf6, 0xf6, 0xf6, 0xf8, 0xfc, 0x00, 0x04, 0x07, 0x0a,
  0x0b, 0x0a, 0x07, 0x04, 0x00, 0xfb, 0xf8, 0xf5, 0xf5, 0xf5, 0xf8, 0xfb,
  0x00, 0x04, 0x08, 0x0b, 0x0c, 0x0b, 0x08, 0x04, 0x00, 0xfb, 0xf7, 0xf4,
  0xf4, 0xf4, 0xf7, 0xfb, 0x00, 0x04, 0x09, 0x0c, 0x0d, 0x0c, 0x09, 0x04,
  0x00, 0xfb, 0xf6, 0xf3, 0xf3, 0xf3, 0xf6, 0xfb, 0x00, 0x05, 0x09, 0x0c,
  0x0e, 0x0c, 0x09, 0x05, 0x00, 0xfa, 0xf6, 0xf3, 0xf2, 0xf3, 0xf6, 0xfa,
  0x00, 0x05, 0x0a, 0x0d, 0x0f, 0x0d, 0x0a, 0x05, 0x00, 0xfa, 0xf5, 0xf2,
  0xf1, 0xf2, 0xf5, 0xfa
]

def song2fur(info,pat_rows,sub_song,ins_pos):
    ins = 0
    break_later = False
    vib_ins = []
    while True:
        if break_later: break
        pointer = rom_data[(ins_pos&0x3fff)+(ins<<1)]
        pointer |= rom_data[(ins_pos&0x3fff)+(ins<<1)+1]<<8
        pointer &= 0x3fff
        pointer_end = rom_data[(ins_pos&0x3fff)+(ins<<1)+2]
        pointer_end |= rom_data[(ins_pos&0x3fff)+(ins<<1)+3]<<8
        pointer_end &= 0x3fff
        if not (pointer_end > pointer and (pointer_end-pointer) < 128 and (pointer_end-pointer) > 0):
            break_later = True
        ins_data = rom_data[pointer:pointer+8]
        if ins_data[0] & 0x20 == 0x20:
            print(ins,bin(ins_data[4]))
            hi = (ins_data[4]>>4&0xf)>>1
            lo = int((ins_data[4]&0xf)/1.5)
            vib_ins.append(hi|lo<<4)
        else:
            vib_ins.append(0)
        ins += 1

    ins_amt = ins
    print(ins_amt)

    ins_data = rom_data[pointer:pointer+256]
    ins_data2 = ins_data

    wav_amt = 128
    wav_pos = []
    ins_use = [[],[],[],[]]

    pattern = [0]*7
    command = [0]*3
    transpose = [0]*3
    romPos = 0
    curChan = 0
    lowNibble = 0
    highNibble = 0
    patSize = 0
    curNote = 0
    channel_pos = [0]*4
    file_name = "out%s.fur"%str(sub_song)
    global f
    f = open(file_name,"wb")

    fprintf(f, "-Furnace module-")

    write16(144)

    write16(0x00)

    write32(0x20)

    for i in range(8): write8(0)

    fprintf(f, "INFO")
    o = f.tell()
    write32(0)

    write8(0)
    write8(1)
    write8(1)
    write8(1)

    write32(0x42700000)

    write16(pat_rows)
    write16(info[0])

    write8(4)
    write8(16)

    write16(ins_amt)
    write16(wav_amt)
    write16(0)

    write32(4*info[0])

    write8(0x04)
    for i in range(31): write8(0)

    for i in range(32): write8(0x40)
    for i in range(32): write8(0x00)

    for i in range(128): write8(0x00)

    write8(0)
    write8(0)

    write32(0x43DC0000)

    flags = [
        0x00, 0x00, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01
    ]

    for i in range(20): write8(flags[i])

    ins_pointer_pos = f.tell()
    for i in range(4*ins_amt): write8(0)

    pointer_pos = f.tell()
    for i in range(4*wav_amt): write8(0)

    pattern_pos = f.tell()
    for i in range(4*info[0]*4): write8(0)

    for i in range(4): 
        for j in range(info[0]): 
            write8(j)

    for i in range(4): write8(2)

    for i in range(4): write8(3)
    for i in range(4): write8(0)

    for i in range(4*2): write8(0)

    write8(0)

    write32(0x3F800000)

    flags2 = [
        0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01,
        0x00, 0x00, 0x01, 0x00, 0x00, 0x01, 0x04, 
        0x00, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00,
        0x00, 0x02, 0x00, 0x01, 0x00, 0x00, 0x00
    ]

    for i in range(28): write8(flags2[i])

    write16(150)
    write16(150)

    write8(0)
    write8(0)

    write8(0)

    for i in range(3): write8(0)

    fprintf(f, "Game Boy")
    write8(0)

    write8(0)
    write8(0)
    write8(0)
    write8(0)
    write8(0)

    write32(0x3F800000)
    write32(0x00000000)
    write32(0x00000000)

    write32(0x00000022)

    write32(0)

    write32(0x010001)

    for i in range(16): write32(0xFFD00000|i)
    for i in range(16): write32(0xFFE00000|i)

    write8(1)

    for i in range(8): write8(0)
    
    write8(1)

    for i in range(16): write8(6)

    write8(0)

    o2 = f.tell()
    f.seek(o,0)
    write32(o2-o)
    f.seek(0,2)

    o2 = f.tell()
    f.seek(pattern_pos)
    write32(o2)
    f.seek(0,2)

    wavetable_header = [
        0x57, 0x41, 0x56, 0x45, 0x8D, 0x00, 0x00,
        0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00
    ]

    has_played = [False]*4

    wav_len = 0
    romPos = info[1] % bank_size
    for i in range(4*info[0]): 
        fprintf(f, "PATR")
        s = f.tell()
        write32(0)

        write16(i&3)
        write16(i>>2)

        write16(0)
        write16(0)

        if (i&3) == 0:
            if trFix == 0:
                for index in range(7):
                    pattern[index] = rom_data[romPos + index]

                
                channel_pos[0] = seq_list[pattern[0]]
                transpose[0] = pattern[1]
                channel_pos[1] = seq_list[pattern[2]]
                transpose[1] = pattern[3]
                channel_pos[2] = seq_list[pattern[4]]
                transpose[2] = pattern[5]
                channel_pos[3] = seq_list[pattern[6]]
                romPos += 7

            else:
                for index in range(11):
                    if index == 0:
                        pattern[0] = rom_data[romPos + index]|(rom_data[romPos + index+1]<<8)
                    elif index == 2:
                        pattern[1] = rom_data[romPos + index]
                    elif index == 3:
                        pattern[2] = rom_data[romPos + index]|(rom_data[romPos + index+1]<<8)
                    elif index == 5:
                        pattern[3] = rom_data[romPos + index]
                    elif index == 6:
                        pattern[4] = rom_data[romPos + index]|(rom_data[romPos + index+1]<<8)
                    elif index == 8:
                        pattern[5] = rom_data[romPos + index]
                    elif index == 9:
                        pattern[6] = rom_data[romPos + index]|(rom_data[romPos + index+1]<<8)
                
                channel_pos[0] = pattern[0] - bankAmt
                transpose[0] = pattern[1]
                channel_pos[1] = pattern[2] - bankAmt
                transpose[1] = pattern[3]
                channel_pos[2] = pattern[4] - bankAmt
                transpose[2] = pattern[5]
                channel_pos[3] = pattern[6] - bankAmt
                romPos += 11

        for rowsLeft in range(pat_rows):
            curChan = i&3
            pat_buffer = [0x0000,0x0000,0xFFFF,0xFFFF,0xFFFF,0xFFFF,0xFFFF,0xFFFF]
            command[0] = rom_data[channel_pos[curChan]]
            command[1] = rom_data[channel_pos[curChan] + 1]
            command[2] = rom_data[channel_pos[curChan] + 2]

            if command[0] == 0:
                pat_buffer[0] = 0
                pat_buffer[1] = 0
                channel_pos[curChan] += 1
                patSize += 1

                    
            elif command[0] > 0 and command[0] < 0x40:
                glide_num = command[0]+37
                pat_buffer[0] = glide_num-NOTE_TRANS
                pat_buffer[4] = 0x03
                pat_buffer[5] = 0xFF
                channel_pos[curChan] += 1
                patSize += 3

                    
            elif command[0] == 0x40:
                lowNibble = (command[1] >> 4)
                highNibble = (command[1] & 15)

                if curChan != 2:
                    if (lowNibble>>2) == 0x3:
                        pat_buffer[0] = 100
                        pat_buffer[1] = 0
                    else:
                        pat_buffer[3] = do_vol(lowNibble>>2)
                else:
                    if [0,4,8,15][lowNibble>>2] == 0:
                        pat_buffer[0] = 100
                        pat_buffer[1] = 0
                    else:
                        pat_buffer[3] = [0,4,8,15][lowNibble>>2]


                channel_pos[curChan] += 2
                patSize += 3

                    
            elif command[0] > 0x40 and command[0] < 0x80:
                curNote = command[0]-28
                if curChan == 0 or curChan == 1 or curChan == 2:
                    curNote += conv_int8(transpose[curChan])
                curNote -= NOTE_TRANS
                pat_buffer[0] = (curNote%12)+1
                pat_buffer[1] = (curNote-(curNote%12))/12
                pat_buffer[2] = (command[1]&0x3f)-1
                if curChan == 2: pat_buffer[3] = wav_vol[command[1]>>6]
                else: pat_buffer[3] = do_vol(command[1]>>6)

                if (command[1]&0x3f) != 0:
                    ins_use[curChan].append(max((command[1]&0x3f)-1,0))
                    has_played[curChan] = True
                elif has_played[curChan]:
                    pat_buffer[4] = 0x03
                    pat_buffer[5] = 0xFF
                channel_pos[curChan] += 2
                patSize += 3

                    
            elif command[0] == 0x80:
                lowNibble = (command[1] >> 4)
                highNibble = (command[1] & 15)


                pat_buffer[6] = 0x0F
                pat_buffer[7] = lowNibble
                channel_pos[curChan] += 2
                patSize += 3
                    
                    
            elif command[0] > 0x80 and command[0] < 0xC0:
                curNote = command[0] - 0x40
                if curChan != 3:
                    curNote += conv_int8(transpose[curChan])
                curNote -= NOTE_TRANS
                pat_buffer[0] = (curNote%12)+1
                pat_buffer[1] = (curNote-(curNote%12))/12
                pat_buffer[2] = (command[1]&0x3f)-1
                if (command[1]&0x3f) != 0:
                    ins_use[curChan].append(max((command[1]&0x3f)-1,0))
                    has_played[curChan] = True
                elif has_played[curChan]:
                    pat_buffer[4] = 0x03
                    pat_buffer[5] = 0xFF

                if curChan == 2: pat_buffer[3] = wav_vol[command[1]>>6&3]
                else: pat_buffer[3] = do_vol(command[1]>>6)

                channel_pos[curChan] += 2
                patSize += 3

                    
            elif command[0] >= 0xC0:
                curNote = command[0] - 156
                lowNibble = (command[2] >> 4)
                highNibble = (command[2] & 15)
                if curChan != 3:
                    curNote += conv_int8(transpose[curChan])
                curNote -= NOTE_TRANS
                pat_buffer[0] = (curNote%12)+1
                pat_buffer[1] = (curNote-(curNote%12))/12
                pat_buffer[2] = (command[1]&0x3f)-1
                if curChan == 2: pat_buffer[3] = wav_vol[command[1]>>6&3]
                else: pat_buffer[3] = do_vol(command[1]>>6)

                pat_buffer[6] = 0x0F
                pat_buffer[7] = lowNibble
                if (command[1]&0x3f) != 0:
                    ins_use[curChan].append(max((command[1]&0x3f)-1,0))
                    has_played[curChan] = True
                elif has_played[curChan]:
                    pat_buffer[4] = 0x03
                    pat_buffer[5] = 0xFF

                channel_pos[curChan] += 3
                patSize += 5

            for byt in range(8): 
                write16(pat_buffer[byt])    

        write8(0)
        s2 = f.tell()
        f.seek(s)
        write32(s2-s)
        f.seek(pattern_pos+(i*4))
        write32(s-4)
        f.seek(0,2)



    for i in range(wav_amt): 
        s = f.tell()
        f.write(bytearray(wavetable_header))
        wav_pos.append(f.tell())
        for j in range(32): 
            write32(0)
        f.seek(pointer_pos+(i*4))
        write32(s)
        f.seek(0,2)

    wav_last_len = 0
    all_wavs = []

    for ins in range(ins_amt):
        pointer = rom_data[(ins_pos&0x3fff)+(ins<<1)]
        pointer |= rom_data[(ins_pos&0x3fff)+(ins<<1)+1]<<8
        pointer &= 0x3fff
        pointer_end = rom_data[(ins_pos&0x3fff)+(ins<<1)+2]
        pointer_end |= rom_data[(ins_pos&0x3fff)+(ins<<1)+3]<<8
        pointer_end &= 0x3fff
        ins_data = rom_data[pointer:pointer+256]
        ins_data2 = ins_data

        if ins_data[1] & 0x80 == 0x80:
            ins_data2 = ins_data2[2:]
        elif ins_data[0] & 0x20 == 0x20:
            ins_data2 = ins_data2[2:]

        wav_header = ins_data2[3:14]
        wav_pointer = wav_header[9]|(wav_header[10]<<8)
        wav_pointer += wav_header[2]
        wav = []
        wav_loop_start = 0xFF
        if ins in ins_use[2]:
            ins_data2 = ins_data2[11:]
            update_rate = max(wav_header[8]-1,0)
            sweep_loop = wav_header[6]
            if update_rate == 0:
                sweep_len = 1
            elif sweep_loop > 0:
                sweep_len = (sweep_loop-wav_header[2])//(max(abs(conv_int8(wav_header[0])),1))+1
            else:
                sweep_len = 16-wav_header[2]

            for j in range(sweep_len):
                start_wav = (wav_pointer&0x3fff)+(j*conv_int8(wav_header[0]))
                current_wav = rom_data[start_wav:start_wav+16]
                if current_wav in all_wavs:
                    wav.append(all_wavs.index(current_wav))
                else:
                    f.seek(wav_pos[wav_last_len])
                    temp = []
                    for i in range(16):
                        temp.append((rom_data[start_wav+i]>>4)&0xf)
                        temp.extend([0]*3)
                        temp.append((rom_data[start_wav+i]>>0)&0xf)
                        temp.extend([0]*3)
                    wav.append(wav_last_len)
                    wav_last_len += 1
                    all_wavs.append(current_wav)
                    f.write(bytearray(temp))
            if update_rate > 0: #sweep_loop > 0 and update_rate > 0:
                wav_loop_start = len(wav)
                sweep_end = (wav_header[4]-wav_header[2])//(max(abs(conv_int8(wav_header[0])),1))+1
                for j in range(sweep_len,sweep_end,-1):
                    start_wav = (wav_pointer&0x3fff)+(j*conv_int8(wav_header[0]))
                    current_wav = rom_data[start_wav:start_wav+16]
                    if current_wav in all_wavs:
                        wav.append(all_wavs.index(current_wav))
                    else:
                        f.seek(wav_pos[wav_last_len])
                        temp = []
                        for i in range(16):
                            temp.append((rom_data[start_wav+i]>>4)&0xf)
                            temp.extend([0]*3)
                            temp.append((rom_data[start_wav+i]>>0)&0xf)
                            temp.extend([0]*3)
                        wav.append(wav_last_len)
                        wav_last_len += 1
                        all_wavs.append(current_wav)
                        f.write(bytearray(temp))
                for j in range(sweep_end,sweep_len):
                    start_wav = (wav_pointer&0x3fff)+(j*conv_int8(wav_header[0]))
                    current_wav = rom_data[start_wav:start_wav+16]
                    if current_wav in all_wavs:
                        wav.append(all_wavs.index(current_wav))
                    else:
                        f.seek(wav_pos[wav_last_len])
                        temp = []
                        for i in range(16):
                            temp.append((rom_data[start_wav+i]>>4)&0xf)
                            temp.extend([0]*3)
                            temp.append((rom_data[start_wav+i]>>0)&0xf)
                            temp.extend([0]*3)
                        wav.append(wav_last_len)
                        wav_last_len += 1
                        all_wavs.append(current_wav)
                        f.write(bytearray(temp))
            print([hex(i) for i in wav_header])
        if len(wav) > 255: wav = wav[:255]
        ins_table = ins_data2[3:(((ins_data[0]&0x1f)*3)+3)]
        vol = []
        arp = []
        duty = []
        loop = 0xFF
        if True:
            print("=== Instrument",hex(ins)[2:].upper(),"===")
            print(hex(pointer),hex(pointer_end))
            i = 0

            cur = [ins_data[2]>>4,0,0]
            if ins in ins_use[2]:
                cur[0] = [0,3,2,1][ins_data[2]>>5&3]

            frame = 1
            #speed = 1 if ins_data[1] & 0x80 else ins_data[1]&7
            speed = ins_data[1]&7
            print([hex(i) for i in ins_data[:8]])
            print([hex(i) for i in ins_table])
            wait = speed
            while i < len(ins_table):
                #print(ins_table[i:i+3])
                do_loop = False
                j = ins_table[i]
                if (j>>4) == 0x8:
                    loop = frame-(j&0xf)
                    print("Jump to",loop)
                    do_loop = True
                elif (j>>4) == 0xC:
                    cur[2] = j&3
                    print("Set duty to",j&0xf)
                elif (j>>4) >= 0x4 and (j>>4) < 8:
                    if j != 0x40:
                        print("Arpeggio abs",hex(j))
                        #pitch = GHX_noise[((j&0x3f)-1)>>1]
                        if ins in ins_use[3]:
                            pitch = GHX_noise[((j&0x3f)-2)>>1]
                            ind = min(FUR_noise, key=lambda x:abs((x&7)-(pitch&7))+abs(((x>>4)&15)-((pitch>>4)&15)))
                            cur[1] = (FUR_noise.index(ind)-22)|(1<<30)  
                            cur[2] = ((pitch&8)>>3)
                        else:
                            cur[1] = (j&0x3f)|(1<<30)
                elif j > 0 and j < 0x80:
                    print("Arpeggio",j)
                    cur[1] = j        
                i += 1

                j = ins_table[i]
                if (j>>4) == 0x8:
                    loop = frame-(j&0xf)
                    print("Jump to",loop)
                    do_loop = True
                elif (j>>4) == 0xC:
                    cur[2] = j&3
                    print("Set duty to",j&0xf)
                elif (j>>4) == 0x4:
                    cur[0] = j&15
                    print("Set volume to",j&0xf)
                elif j != 0:
                    wait = j
                i += 1  
                print("Chunk is",wait,"frames long")

                j = ins_table[i]
                if j == 0:
                    print("Empty")
                elif (j>>4) == 0x8:
                    loop = frame-(j&0xf)
                    print("Jump to",loop)
                    do_loop = True
                elif (j>>4) == 0xC:
                    cur[2] = j&3
                    print("Set duty to",j&0xf)
                elif (j>>4) == 0x4:
                    cur[0] = j&15
                    print("Set volume to",j&0xf)
                else:
                    print("UNKNOWN",hex(j)[2:]) 


                i += 1   
                frame += 1

                for j in range(wait):
                    arp.append(cur[1])
                    duty.append(cur[2])
                    if ins in ins_use[2]:
                        vol.append([0,4,8,15][int(cur[0])])
                    else: 
                        vol.append(int(cur[0]))
                        if (ins_data[2]&0x7) != 0:
                            if (ins_data[2]>>3)&1:
                                cur[0] += 64/60/(ins_data[2]&0x7)
                            else:
                                cur[0] -= 64/60/(ins_data[2]&0x7)
                        cur[0] = max(min(cur[0],15),0)

                print("---")

                if do_loop:
                    break

        for i in range(64):
            if ins in ins_use[2]:
                vol.append([0,4,8,15][int(cur[0])])
            else: 
                vol.append(int(cur[0]))
                if (ins_data[2]&0x7) != 0:
                    if (ins_data[2]>>3)&1:
                        cur[0] += 64/60/(ins_data[2]&0x7)
                    else:
                        cur[0] -= 64/60/(ins_data[2]&0x7)
                    cur[0] = max(min(cur[0],15),0)

        vol = vol[:min(255,len(vol))]
        arp = arp[:min(255,len(arp))]
        duty = duty[:min(255,len(duty))]


        
        pitch = []

        if ins_data[1] & 0x80 == 0x80 or ins_data[0] & 0x20 == 0x20:
            pitch += [0]*ins_data[3]
            vib_pos = 0
            while len(pitch) < 256:
                vib_pos += ins_data[4]&0xf
                vib_pos &= 0x3f
                pitch.append(vibrato_table[(vib_pos>>2&0xf)|(ins_data[4]&0xf0)])
                if (vib_pos>>2) == 0: break

        pitch = pitch[:min(255,len(pitch))]

        loop = max(loop,0)

        insfile = []

        insfile.extend("INS2".encode("ascii"))
        insfile.extend([0]*4)
        insfile.extend([196,0])
        insfile.extend([2,0])
        insfile.extend("GB".encode("ascii"))
        insfile.extend([4,0])
        insfile.extend([(ins_data[2]>>4)|(((ins_data[2]&0x7))<<5),64,1,0])

        insfile.extend("MA".encode("ascii"))
        macro_length = len(insfile)
        insfile.extend([0,0])

        insfile.extend([8,0])
        insfile.extend([0,len(vol)])
        insfile.extend([0xFF,0xFF]) # first element is macro loop
        insfile.extend([0,1,0,1])
        insfile.extend(bytearray(vol))

        insfile.extend([1,len(arp)])
        insfile.extend([loop,0xFF]) # first element is macro loop
        insfile.extend([0,(3<<6)|1,0,1])
        for i in arp:
            insfile.extend([i&0xff,i>>8&0xff,i>>16&0xff,i>>24&0xff])

        insfile.extend([2,len(duty)])
        insfile.extend([loop,0xFF]) # first element is macro loop
        insfile.extend([0,1,0,1])
        insfile.extend(bytearray(duty))

        if ins in ins_use[2]: 
            insfile.extend([3,len(wav),wav_loop_start,0xFF,0,1,0,max(update_rate+1,1)])
            insfile.extend(wav)

        if len(pitch) != 0:
            insfile.extend([4,len(pitch)])
            insfile.extend([ins_data[3],0xFF]) # first element is macro loop
            insfile.extend([0,(1<<6)|1,0,1])
            insfile.extend(bytearray(pitch))

        insfile.extend([0xFF])

        actual_macro_length = len(insfile)-macro_length
        for I in range(2):
            insfile[macro_length+I] = (actual_macro_length>>(I<<3))&0xff
        ins_block_len = len(insfile)-8
        for I in range(4):
            insfile[I+4] = (ins_block_len>>(I<<3))&0xff

        f.seek(0,2)
        POS = f.tell()
        f.write(bytearray(insfile))
        f.seek(ins_pointer_pos+(ins*4))
        write32(POS)

    f.close()

found_magic = False
for i in range(bank_size-len(magic_bytes)):
    if rom_data[i:i+len(magic_bytes)] == magic_bytes:
        header_offset = -1
        for j in range(i,bank_size-len(header_bytes)):
            if rom_data[j:j+len(header_bytes)] == header_bytes:
                header_offset = j
                print("GHX header found at $"+hex(j+bank*bank_size)[2:])
        if header_offset != -1:
            found_magic = True
            num_songs = rom_data[header_offset + 3]
            if num_songs == 0: num_songs = 1
            pat_len = rom_data[header_offset + 4]
            pat_table = rom_data[header_offset + 6]|(rom_data[header_offset + 7]<<8)
            ins_table = rom_data[header_offset + 8]|(rom_data[header_offset + 9]<<8)
            song_table = rom_data[header_offset + 10]|(rom_data[header_offset + 11]<<8)

            pat_table %= bank_size
            ins_table %= bank_size
            song_table %= bank_size

            print("Number of songs:",num_songs)
            print("Pattern row length:",pat_len)
            print("Pattern table pos: $"+hex(pat_table+bank*bank_size)[2:])
            print("Instrument table pos: $"+hex(ins_table+bank*bank_size)[2:])
            print("Song table pos: $"+hex(song_table+bank*bank_size)[2:])
            seq_list = get_seq_list(pat_table)

            for sub_song in range(num_songs):
                rom_pos = song_table+sub_song*6
            
                song_info = []
                song_info.append(rom_data[rom_pos]+1)
                song_info.append(rom_data[rom_pos + 1]|(rom_data[rom_pos + 2]<<8))
                song_info.append(rom_data[rom_pos + 3])
                song_info.append(rom_data[rom_pos + 4]|(rom_data[rom_pos + 5]<<8))
                print("Number of patterns:",str(song_info[0]))
                print("Song data pos: $"+hex(song_info[1])[2:])
                print("Loop pattern relative to final pattern:",str(song_info[2]))
                print("Pattern loop pos: $"+hex(song_info[3])[2:])

                if song_info[0] < 128:
                    song2fur(song_info,pat_len,sub_song,ins_table)
                else:
                    print("Invalid song, skipping")
        else:
            print("Cannot find GHX header!")
            break
    else:
        continue

if not found_magic:
    print("Cannot find magic bytes!")
