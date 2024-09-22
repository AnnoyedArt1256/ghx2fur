import sys, math
f = open("wav_pos.bin","rb")
wav_pos = []
r = f.read(4)
while r:
    r = list(r)
    wav_pos.append(r[0]|(r[1]<<8)|(r[2]<<16)|(r[3]<<24))
    r = f.read(4)
f.close()

f = open("ins_use.bin","rb")
ins_use = {0: [], 1: [], 2: [], 3: []}
for i in list(f.read()):
    ins_use[i>>6].append(i&0x3f)
f.close()
print(ins_use[2])
f = open("ins_table.bin","rb")
ins_pos = int(f.read(1)[0])
ins_pos |= int(f.read(1)[0])<<8
length = int(f.read(1)[0])
length |= int(f.read(1)[0])<<8
code_data = list(f.read(length))
f.close()
print(hex(ins_pos))
pointer = 0xc01
pointer_end = 0xc10
ins = 0

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

break_later = False
while True:
    if break_later: break
    pointer = code_data[(ins_pos&0x3fff)+(ins<<1)]
    pointer |= code_data[(ins_pos&0x3fff)+(ins<<1)+1]<<8
    pointer &= 0x3fff
    pointer_end = code_data[(ins_pos&0x3fff)+(ins<<1)+2]
    pointer_end |= code_data[(ins_pos&0x3fff)+(ins<<1)+3]<<8
    pointer_end &= 0x3fff
    if not (pointer_end > pointer and (pointer_end-pointer) < 128 and (pointer_end-pointer) > 0):
        break_later = True
    ins_data = code_data[pointer:pointer+256]
    ins_data2 = ins_data

    if ins_data[1] & 0x80 == 0x80:
        ins_data2 = ins_data2[2:]
    elif ins_data[0] & 0x20 == 0x20:
        ins_data2 = ins_data2[2:]

    wav_header = ins_data2[3:14]
    wav_pointer = wav_header[9]|(wav_header[10]<<8)
    wav_pointer += wav_header[2]

    if ins in ins_use[2]:
        ins_data2 = ins_data2[11:]
        F = open("out.fur","r+b")
        F.seek(wav_pos[ins])
        temp = []
        for i in range(16):
            temp.append((code_data[(wav_pointer&0x3fff)+i]>>4)&0xf)
            temp.extend([0]*3)
            temp.append((code_data[(wav_pointer&0x3fff)+i]>>0)&0xf)
            temp.extend([0]*3)
        F.write(bytearray(temp))
        F.close()
        print([hex(i) for i in wav_header])

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
            cur[0] = ins_data[2]>>5&3

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
                        print(hex(pitch))
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
                    vol.append([0,15,8,4][int(cur[0])])
                else: 
                    vol.append(int(cur[0]))
                    if (ins_data[2]&0x7) != 0:
                        cur[0] -= 64/60/(ins_data[2]&0x7)
                    cur[0] = max(cur[0],0)

            print("---")

            if do_loop:
                break

    for i in range(64):
        if ins in ins_use[2]:
            vol.append([0,15,8,4][int(cur[0])])
        else: 
            vol.append(int(cur[0]))
            if (ins_data[2]&0x7) != 0:
                cur[0] -= 64/60/(ins_data[2]&0x7)
            cur[0] = max(cur[0],0)
    vol = vol[:min(255,len(vol))]
    arp = arp[:min(255,len(arp))]
    duty = duty[:min(255,len(duty))]

    loop = max(loop,0)

    with open("ins/ins_%d.fui" % ins, "wb") as insfile:
        insfile.write("FINS".encode("ascii"))
        insfile.write(bytearray([196,0]))
        insfile.write(bytearray([2,0]))
        insfile.write("GB".encode("ascii"))
        insfile.write(bytearray([4,0]))
        insfile.write(bytearray([(ins_data[2]>>4)|(((ins_data[2]&0x7))<<5),64,1,0]))

        insfile.write("MA".encode("ascii"))
        macro_length = insfile.tell()
        insfile.write(bytearray([0,0]))

        insfile.write(bytearray([8,0]))
        insfile.write(bytearray([0,len(vol)]))
        insfile.write(bytearray([0xFF,0xFF])) # first element is macro loop
        insfile.write(bytearray([0,1,0,1]))
        insfile.write(bytearray(vol))

        insfile.write(bytearray([1,len(arp)]))
        insfile.write(bytearray([loop,0xFF])) # first element is macro loop
        insfile.write(bytearray([0,3<<6,0,1]))
        for i in arp:
            insfile.write(bytearray([i&0xff,i>>8&0xff,i>>16&0xff,i>>24&0xff]))

        insfile.write(bytearray([2,len(duty)]))
        insfile.write(bytearray([loop,0xFF])) # first element is macro loop
        insfile.write(bytearray([0,1,0,1]))
        insfile.write(bytearray(duty))

        insfile.write(bytearray([3,1,0xFF,0xFF,0,1,0,1,ins]))

        insfile.write(bytearray([0xFF]))

        actual_macro_length = insfile.tell()-macro_length
        insfile.seek(macro_length,0)
        insfile.write(bytearray([actual_macro_length&0xff,actual_macro_length>>8&0xff]))
        insfile.seek(0,2)
    ins += 1
