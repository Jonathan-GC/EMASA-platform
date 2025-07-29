# EMASA Platform: Monitor $backend$ 😊

## Environment variables used in settings.py

|Name|Description|
|----|----|
|DEBUG| Default=False|
|SECRET_KEY| Django's secret key|
|DATABASE_URL| Url for the used database |
|ALLOWED_HOSTS| If you're testing, you can write here your localhost|
|DB_PREFIX| Prefix used in the naming of the DB tables |

### DB Prefix usage

1. Import the mixin from the `mixins.py` file:

```python
from .mixins import PrefixMixin
```
2. Add it to your model:
```python
    class YourModel(models.Model, PrefixMixin):
        # Your attributes
```
Results must be something like `"prefix_model_name"`.
