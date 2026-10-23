const books = require("../site/data/books.json");
const covers = [...new Set(books.map(book => book.cover))];

function fixtureBook(index) {
  const source = structuredClone(books[index % books.length]);
  const long = index % 2 === 0;
  source.id = source.slug = `visual-fixture-${index + 1}`;
  source.title = long
    ? { en: `A Long Mixed Engineering Title for Shelf Item ${index + 1} Across Several Words`, ko: `여러 단어로 이어지는 긴 공학 책 제목 ${index + 1} 책장 테스트` }
    : { en: `Short ${index + 1}`, ko: `짧은 제목 ${index + 1}` };
  source.description = index % 3 === 0 ? undefined : { en: `Fixture description ${index + 1}`, ko: `테스트 설명 ${index + 1}` };
  source.subtitle = { en: `Shelf fixture ${index + 1}`, ko: `책장 항목 ${index + 1}` };
  source.cover = covers[index % covers.length];
  source.tags = index % 3 === 0
    ? [`fixture-${index + 1}`, `Long mixed EN KO synthetic keyword set ${index + 1} process integration and reliability`, `공정 통합 및 신뢰성 검증을 위한 긴 합성 키워드 ${index + 1}`]
    : index % 2 === 0 ? [`fixture-${index + 1}`, `공정 통합 키워드 ${index + 1}`] : [`fixture-${index + 1}`];
  if (index === 49) source.title.en = "AnUnbrokenSyntheticEngineeringTitleThatMustWrapWithinTheAvailableMobileDetailWidth";
  if (index === 49) source.tags = ["synthetic keyword", "공정 통합 합성 키워드", "Long mixed EN KO reliability and process-integration keywords for chip wrapping"];
  return source;
}

function fixtureCatalog(count) {
  return Array.from({ length: count }, (_, index) => fixtureBook(index));
}

module.exports = { books, covers, fixtureBook, fixtureCatalog };
