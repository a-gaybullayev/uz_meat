app_name = "uz_meat"
app_title = "Uz Meat"
app_publisher = "UZ MEAT"
app_description = "Digitize the UZ MEAT retail chain: inter-warehouse stock transfer requests with per-warehouse manager approval, POS profiles and roles for the store network"
app_email = "admin@example.com"
app_license = "mit"

# Apps
# ------------------

# cancel_linked_documents() (stock_transfer_request.py, purchase_proposal.py)
# lives in group_core -- see its permissions.py.
required_apps = ["group_core"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "uz_meat",
# 		"logo": "/assets/uz_meat/logo.png",
# 		"title": "Uz Meat",
# 		"route": "/uz_meat",
# 		"has_permission": "uz_meat.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/uz_meat/css/uz_meat.css"
# app_include_js = "/assets/uz_meat/js/uz_meat.js"

# include js, css files in header of web template
# web_include_css = "/assets/uz_meat/css/uz_meat.css"
# web_include_js = "/assets/uz_meat/js/uz_meat.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "uz_meat/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "uz_meat/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "uz_meat.utils.jinja_methods",
# 	"filters": "uz_meat.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "uz_meat.install.before_install"
# after_install = "uz_meat.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "uz_meat.uninstall.before_uninstall"
# after_uninstall = "uz_meat.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "uz_meat.utils.before_app_install"
# after_app_install = "uz_meat.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "uz_meat.utils.before_app_uninstall"
# after_app_uninstall = "uz_meat.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "uz_meat.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["uz_meat.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

fixtures = [
	{
		# UOM read access for cashiers -- see
		# patches/grant_uom_read_to_store_staff.py for why this is scoped to
		# our own role instead of widening Sales User/Accounts User.
		"dt": "Custom DocPerm",
		"filters": [["parent", "=", "UOM"], ["role", "=", "UZ MEAT Store Staff"]],
	},
]

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"uz_meat.tasks.all"
# 	],
# 	"daily": [
# 		"uz_meat.tasks.daily"
# 	],
# 	"hourly": [
# 		"uz_meat.tasks.hourly"
# 	],
# 	"weekly": [
# 		"uz_meat.tasks.weekly"
# 	],
# 	"monthly": [
# 		"uz_meat.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "uz_meat.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "uz_meat.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "uz_meat.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["uz_meat.utils.before_request"]
# after_request = ["uz_meat.utils.after_request"]

# Job Events
# ----------
# before_job = ["uz_meat.utils.before_job"]
# after_job = ["uz_meat.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"uz_meat.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

