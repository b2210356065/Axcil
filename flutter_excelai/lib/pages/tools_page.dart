import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../services/tool_service.dart';
import '../utils/constants.dart';
import '../utils/theme.dart';

class ToolsPage extends ConsumerStatefulWidget {
  const ToolsPage({super.key});

  @override
  ConsumerState<ToolsPage> createState() => _ToolsPageState();
}

class _ToolsPageState extends ConsumerState<ToolsPage> {
  String? _selectedTool;
  File? _selectedFile;
  final _textController = TextEditingController();
  bool _isProcessing = false;

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles();
    if (result != null) {
      setState(() {
        _selectedFile = File(result.files.single.path!);
      });
    }
  }

  Future<void> _executeTool() async {
    if (_selectedTool == null) {
      _showError('Please select a tool');
      return;
    }

    setState(() {
      _isProcessing = true;
    });

    try {
      final service = ToolService();
      final result = await service.executeTool(
        toolType: _selectedTool!,
        businessId: 1, // TODO: Get from selected business
        functionalityId: 1, // TODO: Get from selected functionality
        file: _selectedFile,
        text: _textController.text.isEmpty ? null : _textController.text,
      );

      if (mounted) {
        _showSuccess('Tool executed successfully!');
        setState(() {
          _selectedFile = null;
          _textController.clear();
        });
      }
    } catch (e) {
      _showError('Error: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
        });
      }
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: AppTheme.error),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: AppTheme.accent),
    );
  }

  Widget _buildToolIcon(String assetPath, Color color) {
    if (assetPath.endsWith('.svg')) {
      // SVG dosyaları için renk uygula
      return SvgPicture.asset(
        assetPath,
        colorFilter: ColorFilter.mode(color, BlendMode.srcIn),
        fit: BoxFit.contain,
      );
    } else {
      // PNG dosyaları için orijinal renkleri koru
      return Image.asset(
        assetPath,
        fit: BoxFit.contain,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tools'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Select Tool',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 16,
              runSpacing: 16,
              children: ApiConstants.toolTypes.map((toolType) {
                final isSelected = _selectedTool == toolType;
                return InkWell(
                  onTap: () {
                    setState(() {
                      _selectedTool = toolType;
                      _selectedFile = null;
                      _textController.clear();
                    });
                  },
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    width: 140,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: isSelected ? AppTheme.primary : AppTheme.surface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isSelected ? AppTheme.primary : AppTheme.border,
                        width: 2,
                      ),
                    ),
                    child: Column(
                      children: [
                        SizedBox(
                          width: 48,
                          height: 48,
                          child: _buildToolIcon(
                            ApiConstants.toolIcons[toolType]!,
                            isSelected ? Colors.white : AppTheme.primary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          ApiConstants.toolNames[toolType]!,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontWeight: FontWeight.w500,
                            color: isSelected ? Colors.white : AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
            if (_selectedTool != null) ...[
              const SizedBox(height: 32),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        ApiConstants.toolNames[_selectedTool]!,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                      if (_selectedTool == 'image' ||
                          _selectedTool == 'pdf' ||
                          _selectedTool == 'voice' ||
                          _selectedTool == 'excel') ...[
                        OutlinedButton.icon(
                          onPressed: _pickFile,
                          icon: const Icon(Icons.upload_file),
                          label: const Text('Select File'),
                        ),
                        if (_selectedFile != null) ...[
                          const SizedBox(height: 8),
                          Text(
                            'Selected: ${_selectedFile!.path.split('/').last}',
                            style: const TextStyle(color: AppTheme.textSecondary),
                          ),
                        ],
                      ],
                      if (_selectedTool == 'text') ...[
                        TextField(
                          controller: _textController,
                          decoration: const InputDecoration(
                            labelText: 'Enter Text',
                            hintText: 'Paste or type your text here...',
                          ),
                          maxLines: 6,
                        ),
                      ],
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _isProcessing ? null : _executeTool,
                          child: _isProcessing
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Text('Generate Excel'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
