class ApiConfig {
  final String? geminiApiKey;
  final String? claudeApiKey;
  final String? openaiApiKey;
  final String defaultModel;

  ApiConfig({
    this.geminiApiKey,
    this.claudeApiKey,
    this.openaiApiKey,
    this.defaultModel = 'gemini',
  });

  factory ApiConfig.fromJson(Map<String, dynamic> json) {
    return ApiConfig(
      geminiApiKey: json['gemini_api_key'],
      claudeApiKey: json['claude_api_key'],
      openaiApiKey: json['openai_api_key'],
      defaultModel: json['default_model'] ?? 'gemini',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'gemini_api_key': geminiApiKey,
      'claude_api_key': claudeApiKey,
      'openai_api_key': openaiApiKey,
      'default_model': defaultModel,
    };
  }

  bool get hasAnyKey {
    return geminiApiKey != null || claudeApiKey != null || openaiApiKey != null;
  }

  bool get isConfigured {
    return geminiApiKey?.isNotEmpty == true ||
        claudeApiKey?.isNotEmpty == true ||
        openaiApiKey?.isNotEmpty == true;
  }
}
