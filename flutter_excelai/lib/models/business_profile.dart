class BusinessProfile {
  final int id;
  final String businessName;
  final String businessDescription;
  final String? sector;
  final bool isActive;
  final DateTime createdAt;

  BusinessProfile({
    required this.id,
    required this.businessName,
    required this.businessDescription,
    this.sector,
    required this.isActive,
    required this.createdAt,
  });

  factory BusinessProfile.fromJson(Map<String, dynamic> json) {
    return BusinessProfile(
      id: json['id'],
      businessName: json['business_name'],
      businessDescription: json['business_description'],
      sector: json['sector'],
      isActive: json['is_active'] ?? true,
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'business_name': businessName,
      'business_description': businessDescription,
      'sector': sector,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
