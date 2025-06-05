---
layout: default
title: Home
---

# Welcome

This is the homepage. 

---

## Recent Posts

<ul>
  {% for post in site.posts %}
    <li>
      <a href="{{ post.url | relative_url }}">
        {{ post.title }}
      </a>
      <span class="post-date">
        ({{ post.date | date: "%b %-d, %Y" }})
      </span>
    </li>
  {% endfor %}
</ul>


---

## Categories

<ul>
  {% for category in site.categories %}
    <li>
      <a href="{{ site.baseurl }}/categories/{{ category[0] | slugify }}/">
        {{ category[0] }}
      </a>
      ({{ category[1].size }} posts)
    </li>
  {% endfor %}
</ul>


---

## About Me

enrique

---

## Quick Links

- [All Posts]({{ site.baseurl }}/blog/)  
- [Projects]({{ site.baseurl }}/projects/)  
- [Contact]({{ site.baseurl }}/contact/)  


---