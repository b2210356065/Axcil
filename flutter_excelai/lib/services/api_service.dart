import 'package:dio/dio.dart';
import '../utils/constants.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  late Dio _dio;

  ApiService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: ApiConstants.connectionTimeout,
      receiveTimeout: ApiConstants.receiveTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    ));

    // Add logging interceptor
    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      error: true,
    ));
  }

  Dio get dio => _dio;

  // Health check
  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get(ApiConstants.health);
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // GET request
  Future<Response> get(String path, {Map<String, dynamic>? params}) async {
    return await _dio.get(path, queryParameters: params);
  }

  // POST request
  Future<Response> post(String path, {dynamic data}) async {
    return await _dio.post(path, data: data);
  }

  // PUT request
  Future<Response> put(String path, {dynamic data}) async {
    return await _dio.put(path, data: data);
  }

  // DELETE request
  Future<Response> delete(String path) async {
    return await _dio.delete(path);
  }

  // Upload file
  Future<Response> uploadFile(String path, String filePath, {
    Map<String, dynamic>? data,
  }) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(filePath),
      ...?data,
    });
    return await _dio.post(path, data: formData);
  }

  // Download file
  Future<void> downloadFile(String url, String savePath) async {
    await _dio.download(url, savePath);
  }
}
