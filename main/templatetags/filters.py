from django import template

register = template.Library()


@register.filter
def average_rating(ratings):
    if not ratings or not hasattr(ratings, 'exists') or not ratings.exists():
        return 0
    total = sum([r.score for r in ratings])
    return round(total / ratings.count(), 1)


@register.filter
def dict_key(d, key):
    return d.get(key, 0)

@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key)
