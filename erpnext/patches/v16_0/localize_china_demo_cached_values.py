from erpnext.setup.china_defaults import (
	localize_bundled_demo_cached_values,
	localize_bundled_demo_data,
)


def execute():
	localize_bundled_demo_data()
	localize_bundled_demo_cached_values()
