# Independent textbook starter

Use the portal's scaffolder to create a separate, independently deployable book repository:

~~~sh
python3 tools/scaffold_book.py \
  --id devicephysicsbook \
  --title-en DevicePhysicsBook \
  --title-ko DevicePhysicsBook \
  --subtitle-en "Semiconductor physics and devices" \
  --subtitle-ko "반도체 물리와 소자" \
  --description-en "A textbook about semiconductor physics and devices." \
  --description-ko "반도체 물리와 소자를 다루는 교재입니다." \
  --repository-url https://github.com/frbread7/devicephysicsbook \
  --production-url https://frbread7.github.io/devicephysicsbook/ \
  --out ../devicephysicsbook
~~~

The generated repository includes a small static landing page, a cover SVG, an independent Pages Actions workflow, a bilingual catalog manifest, and this publication/license reminder. It starts as in-progress with zero chapters and no experiments. It is a scaffold, not a textbook.

The book owner must write and validate the actual chapters, add citations, choose its content/code licenses, test and deploy the work, and publish a reviewed release. Then update chapter entries, available language URLs, cover path, version, tags, prerequisites, related books, and publication evidence in library-manifest.json before registering it in My Library.

The My Library manifest schema is schemas/book.schema.json. The portal registration and expansion steps are in docs/BOOK_FACTORY.md and docs/ADDING_A_NEW_BOOK.md.
