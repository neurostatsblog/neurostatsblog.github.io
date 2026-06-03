---
layout: page
title: Subscribe
permalink: /subscribe/
---

New posts go up roughly every few weeks. Two ways to get them:

## By email

{% if site.buttondown_username and site.buttondown_username != "" %}
<form
  action="https://buttondown.com/api/emails/embed-subscribe/{{ site.buttondown_username }}"
  method="post"
  target="popupwindow"
  onsubmit="window.open('https://buttondown.com/{{ site.buttondown_username }}', 'popupwindow')"
  class="subscribe-form"
>
  <label for="bd-email" class="sr-only">Email address</label>
  <input type="email" name="email" id="bd-email" placeholder="you@example.com" required>
  <button type="submit">Subscribe</button>
</form>

<p class="subscribe-note">
  Powered by <a href="https://buttondown.com" rel="noopener">Buttondown</a>. One email per post, no marketing, unsubscribe any time.
</p>

<style>
  .subscribe-form {
    display: flex;
    gap: 0.5rem;
    max-width: 28rem;
    margin: 1rem 0 0.5rem;
  }
  .subscribe-form input[type="email"] {
    flex: 1;
    padding: 0.55rem 0.75rem;
    border: 1px solid var(--color-border);
    border-radius: 4px;
    background: var(--color-surface);
    color: var(--color-text);
  }
  .subscribe-form input[type="email"]:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 1px;
  }
  .subscribe-form button {
    padding: 0.55rem 1.1rem;
    border: 1px solid var(--color-primary);
    border-radius: 4px;
    background: var(--color-primary);
    color: var(--color-text-inverse);
    font-weight: 500;
  }
  .subscribe-form button:hover { background: var(--color-primary-hover); }
  .subscribe-note { color: var(--color-text-muted); font-size: 0.9rem; }
  .sr-only {
    position: absolute; width: 1px; height: 1px;
    padding: 0; margin: -1px; overflow: hidden;
    clip: rect(0,0,0,0); border: 0;
  }
</style>
{% else %}
Email subscription is not yet configured for this blog. In the meantime, you can use the RSS option below, or paste the feed URL into a service like [Blogtrottr](https://blogtrottr.com/) or [follow.it](https://follow.it/) to get new posts in your inbox.
{% endif %}

## By RSS

If you use a feed reader (Feedly, Inoreader, NetNewsWire, Reeder, etc.), subscribe to the feed:

```
{{ '/feed.xml' | absolute_url }}
```

[Open feed →]({{ '/feed.xml' | relative_url }})
