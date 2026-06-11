# [ebarragan.dev](https://enriquebarragan.github.io)
my personal website.

built with [jekyll](https://jekyllrb.com/), [tailwind CSS](https://tailwindcss.com/), [github pages](https://pages.github.com/)

---

### Local setup

#### Docker

Use this if Ruby is not installed locally:

```powershell
docker run --rm -it `
  -p 4000:4000 `
  -v "${PWD}:/site" `
  -w /site `
  ruby:3.2 `
  bash -lc "bundle install && bundle exec jekyll serve --host 0.0.0.0 --livereload --force_polling"
```

Open <http://localhost:4000>.

#### Ruby

If Ruby and Bundler are installed locally:

```powershell
bundle install
bundle exec jekyll serve --livereload
```

Open <http://localhost:4000>.

---

### License

- Site code is licensed under the [MIT License](LICENSE)
- Original content (writing, images) is licensed under [CC BY-NC 4.0](LICENSE-content.md) 
