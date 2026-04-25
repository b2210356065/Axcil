class ToolResult {
  final int id;
  final String functionalityName;
  final String outputFile;
  final int fileSize;
  final DateTime createdAt;

  ToolResult({
    required this.id,
    required this.functionalityName,
    required this.outputFile,
    required this.fileSize,
    required this.createdAt,
  });

  factory ToolResult.fromJson(Map<String, dynamic> json) {
    return ToolResult(
      id: json['id'],
      functionalityName: json['functionality_name'] ?? 'Unknown',
      outputFile: json['output_file'] ?? '',
      fileSize: json['file_size'] ?? 0,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'functionality_name': functionalityName,
      'output_file': outputFile,
      'file_size': fileSize,
      'created_at': createdAt.toIso8601String(),
    };
  }

  String get fileName => outputFile.split('/').last.split('\\').last;
}
