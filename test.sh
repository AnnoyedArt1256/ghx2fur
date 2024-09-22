gcc ghx2fur.c -lm
#./a.out Jimmy\ White\'s\ Cueball\ \(E\)\ \[C\]\[\!\].gbc 11 $1
#./a.out SpongeBob\ SquarePants\ -\ Legend\ of\ the\ Lost\ Spatula\ \(U\)\ \[C\]\[\!\].gbc 3e $1
./a.out "$1" "$2" "$3"
rm -r ./ins/*.fui
python3 decode_ins.py
