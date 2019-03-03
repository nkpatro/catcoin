#pragma once

uint32_t convert_blob(const char *blob, size_t len, char *out);
bool validate_address(const char *addr, size_t len);