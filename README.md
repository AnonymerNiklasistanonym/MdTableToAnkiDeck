# MdTableToAnkiDeck

Python script that makes it possible to create flashcards in a markdown editor, preview it there and then export it to a anki deck file.

---

If you want to see a quick demo check the demo directory: [Demo](demo)

---

## Explanation

```
Create an anki deck with an input markdown table document
        $ python markdownToAnki.py ./markdownFile -enabledOption

        -d                      Activate debugging
        -out-anki filePath      Custom anki deck output file path
        -out-md filePath        Custom markdown doc output file path
        -resource-prefix prefix Custom image path prefix (if image is
                                in a directory and not root enter the
                                directory as prefix [e.g. "pictures"])
```

## Why does this exist

I wanted to use Anki cards (to sync to Web/Android),  but the whole software thing is not that modern or easy to use.

Then I thought I could just write my flashcards in a markdown table and then simply export them.

- *I use [Typora](https://typora.io/) as Markdown editor (because it also supports **Latex math**)*

So I found a cool python module which could not only add cards to a deck and let me customize the card templates, but also updates cards if they have an unique index!

- This means you can not only add cards any time to the same deck by importing a new build every time you change something, you can even update cards that have wrong information etc.!

## Issues/Improvements/Ideas

Just open an issue and I'll try to make it happen, without any issues I will only add things that I want (have on my mind).
