# Changelog

## 0.1.0

- Initial pyvworld package.
- Added VWorld Search, Geocoder, 2D Data, WMS/WFS, Legend, StaticMap, WMTS, and TMS wrappers.
- Added official 2D Data API 2.0 catalog with 158 service IDs.
- Added offline tests for parameter normalization, HTTP error mapping, endpoint query construction, image/tile URL generation, and catalog integrity.
- Added opt-in live smoke tests for real VWorld server verification.
- Added local `.env` loading via `VworldClient.from_env_file()`.
- Added public enums, typed coordinate models, official StaticMap/Image enum values, and explicit domain override handling for typed external usage.
- Converted public value/response models to frozen Pydantic v2 models while preserving existing constructors and validation exceptions.
- Hid API keys from internal HTTP helper repr output.
- Added README and implementation notes for future maintenance.
