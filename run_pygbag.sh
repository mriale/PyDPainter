
#!/usr/bin/bash

mkdir -p pygbag/libs
cp libs/*.py pygbag/libs/
cp -r data pygbag
cp -r logo pygbag
cp -r iff_pics pygbag
pygbag pygbag
cd ..
