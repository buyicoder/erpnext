from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import requests

from erpnext.accounts.doctype.currency_exchange_settings import currency_exchange_settings


class TestCurrencyExchangeSettingsI18n(TestCase):
	def test_network_error_uses_a_fixed_translatable_template(self):
		document = SimpleNamespace(req_params=[], api_endpoint="https://rates.example.test/latest")
		template = "Exchange rate service call failed: {0}"
		translations = {template: "汇率服务调用失败：{0}"}

		with (
			patch.object(currency_exchange_settings, "nowdate", return_value="2026-08-20"),
			patch.object(
				currency_exchange_settings.requests,
				"get",
				side_effect=requests.exceptions.ConnectionError("service unavailable"),
			),
			patch.object(
				currency_exchange_settings,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(
				currency_exchange_settings.frappe,
				"throw",
				side_effect=RuntimeError,
			) as throw,
			self.assertRaises(RuntimeError),
		):
			currency_exchange_settings.CurrencyExchangeSettings.validate_parameters(document)

		throw.assert_called_once_with("汇率服务调用失败：service unavailable")

	def test_http_status_error_uses_the_same_localized_boundary(self):
		document = SimpleNamespace(req_params=[], api_endpoint="https://rates.example.test/latest")
		response = Mock()
		response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Client Error")
		template = "Exchange rate service call failed: {0}"
		translations = {template: "汇率服务调用失败：{0}"}

		with (
			patch.object(currency_exchange_settings, "nowdate", return_value="2026-08-20"),
			patch.object(currency_exchange_settings.requests, "get", return_value=response),
			patch.object(
				currency_exchange_settings,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(
				currency_exchange_settings.frappe,
				"throw",
				side_effect=RuntimeError,
			) as throw,
			self.assertRaises(RuntimeError),
		):
			currency_exchange_settings.CurrencyExchangeSettings.validate_parameters(document)

		throw.assert_called_once_with("汇率服务调用失败：401 Client Error")

	def test_invalid_json_response_uses_the_same_localized_boundary(self):
		document = SimpleNamespace(req_params=[], api_endpoint="https://rates.example.test/latest")
		response = Mock()
		response.json.side_effect = ValueError("invalid JSON")
		template = "Exchange rate service call failed: {0}"
		translations = {template: "汇率服务调用失败：{0}"}

		with (
			patch.object(currency_exchange_settings, "nowdate", return_value="2026-08-20"),
			patch.object(currency_exchange_settings.requests, "get", return_value=response),
			patch.object(
				currency_exchange_settings,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(
				currency_exchange_settings.frappe,
				"throw",
				side_effect=RuntimeError,
			) as throw,
			self.assertRaises(RuntimeError),
		):
			currency_exchange_settings.CurrencyExchangeSettings.validate_parameters(document)

		throw.assert_called_once_with("汇率服务调用失败：invalid JSON")

	def test_invalid_result_key_includes_the_response_in_chinese(self):
		document = SimpleNamespace(result_key=[SimpleNamespace(key="rate")])
		response = SimpleNamespace(text='{"error":"missing rate"}')
		template = "Invalid result key. Response: {0}"
		translations = {template: "汇率服务返回结果中不存在配置的结果键。响应内容：{0}"}

		with (
			patch.object(
				currency_exchange_settings,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(
				currency_exchange_settings.frappe,
				"throw",
				side_effect=RuntimeError,
			) as throw,
			self.assertRaises(RuntimeError),
		):
			currency_exchange_settings.CurrencyExchangeSettings.validate_result(
				document, response, {}
			)

		throw.assert_called_once_with(
			'汇率服务返回结果中不存在配置的结果键。响应内容：{"error":"missing rate"}'
		)

	def test_non_numeric_result_explains_the_exchange_rate_contract(self):
		document = SimpleNamespace(result_key=[])
		response = SimpleNamespace(text='{"rate":"not-a-number"}')
		template = "The exchange rate service did not return a numeric exchange rate."
		translations = {template: "汇率服务未返回有效的数值汇率。"}

		with (
			patch.object(
				currency_exchange_settings,
				"_",
				side_effect=lambda message: translations.get(message, message),
			),
			patch.object(
				currency_exchange_settings.frappe,
				"throw",
				side_effect=RuntimeError,
			) as throw,
			self.assertRaises(RuntimeError),
		):
			currency_exchange_settings.CurrencyExchangeSettings.validate_result(
				document, response, "not-a-number"
			)

		throw.assert_called_once_with("汇率服务未返回有效的数值汇率。")
