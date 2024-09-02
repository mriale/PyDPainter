for image in `grep -o '[A-Za-z0-9/-]*\.png' menus/src/spacing.md`; do
  git mv menus/src/$image tools/src/$image
done
