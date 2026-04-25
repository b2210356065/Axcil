class Functionality {
  final int id;
  final int businessId;
  final String name;
  final String description;
  final Map<String, dynamic>? enrichedDefinition;
  final String? algorithmPath;
  final int algorithmVersion;
  final List<int> dataTypeIds;

  Functionality({
    required this.id,
    required this.businessId,
    required this.name,
    required this.description,
    this.enrichedDefinition,
    this.algorithmPath,
    this.algorithmVersion = 0,
    this.dataTypeIds = const [],
  });

  factory Functionality.fromJson(Map<String, dynamic> json) {
    return Functionality(
      id: json['id'],
      businessId: json['business_id'],
      name: json['name'],
      description: json['description'],
      enrichedDefinition: json['enriched_definition'] != null
          ? Map<String, dynamic>.from(json['enriched_definition'])
          : null,
      algorithmPath: json['algorithm_path'],
      algorithmVersion: json['algorithm_version'] ?? 0,
      dataTypeIds: json['data_type_ids'] != null
          ? List<int>.from(json['data_type_ids'])
          : [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'business_id': businessId,
      'name': name,
      'description': description,
      'enriched_definition': enrichedDefinition,
      'algorithm_path': algorithmPath,
      'algorithm_version': algorithmVersion,
      'data_type_ids': dataTypeIds,
    };
  }
}
