class ApiConstants {
  // Backend API Base URL
  static const String baseUrl = 'http://127.0.0.1:8000';

  // API Endpoints
  static const String health = '/api/health';
  static const String config = '/api/config';
  static const String businessProfiles = '/api/business';
  static const String functionalities = '/api/functionalities';
  static const String tools = '/api/tools';
  static const String history = '/api/history';
  static const String debug = '/api/debug';

  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 60);

  // Tool Types
  static const List<String> toolTypes = [
    'image',
    'pdf',
    'voice',
    'text',
    'excel',
    'form',
  ];

  // Tool Icons (Asset Paths)
  static const Map<String, String> toolIcons = {
    'image': 'assets/tools/image.svg',
    'pdf': 'assets/tools/pdf.png',
    'voice': 'assets/tools/voice.svg',
    'text': 'assets/tools/text.png',
    'excel': 'assets/tools/excel.png',
    'form': 'assets/tools/form.svg',
  };

  // Tool Names
  static const Map<String, String> toolNames = {
    'image': 'Image to Excel',
    'pdf': 'PDF to Excel',
    'voice': 'Voice to Excel',
    'text': 'Text to Excel',
    'excel': 'Excel Transform',
    'form': 'Smart Form',
  };
}
