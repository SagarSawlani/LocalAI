import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:google_fonts/google_fonts.dart';
import 'dart:convert';
import 'dart:async';
import 'dart:math' as math;

// ── Colour Tokens ──────────────────────────────────────────────────────────
const _bg        = Color(0xFF080D1E);
const _surface   = Color(0xFF111829);
const _surface2  = Color(0xFF1A2235);
const _border    = Color(0xFF2A3450);
const _accent    = Color(0xFF7C72FF);
const _accentEnd = Color(0xFF4158D0);
const _textSec   = Color(0xFF8B9AB5);

void main() {
  runApp(const PocketMindApp());
}

class PocketMindApp extends StatelessWidget {
  const PocketMindApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PocketMind',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: _bg,
        colorScheme: const ColorScheme.dark(
          primary: _accent,
          surface: _surface,
        ),
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
      ),
      home: const ChatScreen(),
    );
  }
}

enum ChatMode { assistant, searchPhone }

class ChatMessage {
  final String text;
  final bool isUser;
  final Map<String, dynamic>? pendingAction;
  bool resolved;
  bool isStreaming;
  final List<String>? filePaths;

  ChatMessage(this.text, this.isUser,
      {this.pendingAction,
      this.resolved = false,
      this.isStreaming = false,
      this.filePaths});
}

// ── Main Screen ───────────────────────────────────────────────────────────
class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _loading = false;
  ChatMode _mode = ChatMode.assistant;
  late AnimationController _loadingController;

  static const String baseUrl = "http://127.0.0.1:8000";

  @override
  void initState() {
    super.initState();
    _loadingController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _loadingController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _openFile(String path) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/docs/open?path=${Uri.encodeQueryComponent(path)}"),
      );
      final data = jsonDecode(response.body);
      if (data["status"] != "opened") {
        setState(() {
          _messages.add(ChatMessage(
              "Couldn't open file: ${data['message'] ?? 'unknown error'}",
              false));
        });
        _scrollToBottom();
      }
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage("Error opening file: $e", false));
      });
      _scrollToBottom();
    }
  }

  void _showModeSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: _surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40, height: 4,
                  decoration: BoxDecoration(
                    color: _border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Text("Switch Mode",
                  style: GoogleFonts.inter(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: Colors.white)),
              const SizedBox(height: 16),
              _modeOption(
                icon: Icons.smart_toy_outlined,
                title: "AI Assistant",
                subtitle: "File ops, rename, move, insights",
                mode: ChatMode.assistant,
              ),
              const SizedBox(height: 12),
              _modeOption(
                icon: Icons.manage_search_rounded,
                title: "Search Phone",
                subtitle: "Ask questions about your documents",
                mode: ChatMode.searchPhone,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _modeOption({
    required IconData icon,
    required String title,
    required String subtitle,
    required ChatMode mode,
  }) {
    final selected = _mode == mode;
    return GestureDetector(
      onTap: () {
        setState(() => _mode = mode);
        Navigator.pop(context);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected ? _accent.withOpacity(0.15) : _surface2,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
              color: selected ? _accent : _border, width: selected ? 1.5 : 1),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                gradient: selected
                    ? const LinearGradient(
                        colors: [_accent, _accentEnd],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight)
                    : null,
                color: selected ? null : _border,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, size: 20, color: Colors.white),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: GoogleFonts.inter(
                          fontWeight: FontWeight.w600,
                          fontSize: 15,
                          color: Colors.white)),
                  const SizedBox(height: 2),
                  Text(subtitle,
                      style: GoogleFonts.inter(
                          fontSize: 12, color: _textSec)),
                ],
              ),
            ),
            if (selected)
              const Icon(Icons.check_circle_rounded,
                  color: _accent, size: 20),
          ],
        ),
      ),
    );
  }

  Future<void> _sendMessage() async {
    final query = _controller.text.trim();
    if (query.isEmpty || _loading) return;

    setState(() {
      _messages.add(ChatMessage(query, true));
      _controller.clear();
    });
    _scrollToBottom();

    if (_mode == ChatMode.searchPhone) {
      await _streamSearch(query);
    } else {
      setState(() => _loading = true);
      await _callAgent(query, autoConfirm: false);
    }
  }

  Future<void> _streamSearch(String query) async {
    setState(() {
      _messages.add(ChatMessage("", false, isStreaming: true));
      _loading = true;
    });
    _scrollToBottom();

    String accumulated = "";

    try {
      final client = http.Client();
      final request = http.Request(
        "GET",
        Uri.parse(
            "$baseUrl/docs/ask/stream?query=${Uri.encodeQueryComponent(query)}"),
      );
      final response = await client.send(request);

      await response.stream.transform(utf8.decoder).forEach((chunk) {
        accumulated += chunk;
        setState(() {
          String display = accumulated;
          if (accumulated.contains("__SOURCES__")) {
             display = accumulated.split("__SOURCES__")[0].trim();
          }
          _messages[_messages.length - 1] = ChatMessage(
            display,
            false,
            isStreaming: true,
          );
        });
        _scrollToBottom();
      });

      setState(() {
        List<String>? paths;
        String finalOutput = accumulated;
        if (accumulated.contains("__SOURCES__")) {
           final parts = accumulated.split("__SOURCES__");
           finalOutput = parts[0].trim();
           paths = parts.length > 1 
               ? parts[1].trim().split("\n").where((s) => s.trim().isNotEmpty).toList()
               : null;
        }

        _messages[_messages.length - 1] =
            ChatMessage(finalOutput, false, isStreaming: false, filePaths: paths);
        _loading = false;
      });
      client.close();
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage("Error: $e", false));
        _loading = false;
      });
    }
    _scrollToBottom();
  }

  Future<void> _callAgent(String query,
      {required bool autoConfirm,
      Map<String, dynamic>? plan,
      int? choiceIndex}) async {
    setState(() => _loading = true);
    try {
      final body = <String, dynamic>{
        "query": query,
        "auto_confirm": autoConfirm,
      };
      if (choiceIndex != null) body["choice_index"] = choiceIndex;

      final response = await http.post(
        Uri.parse("$baseUrl/agent/execute"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );
      final data = jsonDecode(response.body);
      _handleResponse(query, data);
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage("Error: $e", false));
        _loading = false;
      });
    }
    _scrollToBottom();
  }

  void _handleResponse(String originalQuery, Map<String, dynamic> data) {
    final status = data["status"];

    if (status == "needs_confirmation") {
      final tool = data["tool"];
      final plan = data["plan"];
      setState(() {
        _messages.add(ChatMessage(
          "Ready to $tool:\n${_prettyPlan(plan)}",
          false,
          pendingAction: {"plan": plan},
        ));
        _loading = false;
      });
    } else if (status == "needs_choice") {
      final matches = (data["detail"]["matches"] as List).cast<String>();
      setState(() {
        _messages.add(ChatMessage(
          "Multiple matches found:",
          false,
          filePaths: matches,
        ));
        _loading = false;
      });
    } else if (status == "executed") {
      final tool = data["tool"];
      final result = data["result"];
      List<String>? paths;
      String messageText = "Done.";

      if (tool == "locate_file") {
        final results = (result["results"] as List?) ?? [];
        paths = results.map((r) => r["path"] as String).toList();
        messageText = paths.isEmpty
            ? "Couldn't find any matching files."
            : "Found ${paths.length} file(s) matching your query.";
      } else if (tool == "photo_search") {
        final results = (result as List?) ?? [];
        paths = results.map((r) => r["path"] as String).toList();
        messageText = paths.isEmpty
            ? "No matching photos found."
            : "Found ${paths.length} photo(s) matching your description.";
      } else if (tool == "search_documents") {
        final answer = result["answer"] as String? ?? "No answer found.";
        final sources = (result["sources"] as List?) ?? [];
        paths = sources.map((s) => s["path"] as String).toList();
        messageText = answer;
      } else if (tool == "scan") {
        if (result is List) {
          messageText = "Found ${result.length} item(s).";
          paths = result.map((r) => r["path"] as String).toList();
        } else if (result is Map && result["error"] != null) {
          messageText = "❌ ${result["error"]}";
        } else {
          messageText = "No items found.";
        }
      } else if (tool == "insights") {
        final total = result["total_size_readable"] ?? "?";
        final totalFiles = result["total_files"] ?? "?";
        final categories = (result["by_category"] as List?) ?? [];
        final catSummary = categories
            .map((c) =>
                "• ${c['category']}: ${c['count']} files (${c['size_readable']})")
            .join("\n");
        messageText =
            "Storage Insights\n$totalFiles files · $total total\n\n$catSummary";
      } else if (tool == "find_duplicates") {
        final groups = (result["duplicate_groups"] as List?) ?? [];
        messageText = groups.isEmpty
            ? "No duplicates found!"
            : "Found ${groups.length} group(s) of duplicate files.";
      } else if (tool == "delete") {
        messageText = "Deleted successfully.";
      } else if (tool == "move" || tool == "rename") {
        final path = result["to"] as String?;
        if (path != null) {
          paths = [path];
          messageText =
              tool == "move" ? "File moved successfully." : "File renamed successfully.";
        }
      }

      setState(() {
        _messages.add(ChatMessage(messageText, false, filePaths: paths));
        _loading = false;
      });
    } else if (status == "error" || status == "failed") {
      final reason = data["reason"] ?? data["detail"] ?? "Unknown error";
      setState(() {
        _messages.add(ChatMessage(
            reason is String ? reason : jsonEncode(reason), false));
        _loading = false;
      });
    } else {
      setState(() {
        _messages.add(ChatMessage(jsonEncode(data), false));
        _loading = false;
      });
    }
    _scrollToBottom();
  }

  String _prettyPlan(Map<String, dynamic> plan) {
    return plan.entries
        .where((e) => e.key != "status" && e.key != "tool")
        .map((e) => "${e.key}: ${e.value}")
        .join("\n");
  }

  Future<void> _confirmAction(ChatMessage msg) async {
    setState(() {
      msg.resolved = true;
      _loading = true;
    });
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/agent/execute-plan"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"plan": msg.pendingAction!["plan"]}),
      );
      final data = jsonDecode(response.body);
      _handleResponse("", data);
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage("Error: $e", false));
        _loading = false;
      });
    }
    _scrollToBottom();
  }

  void _cancelAction(ChatMessage msg) {
    setState(() {
      msg.resolved = true;
      _messages.add(ChatMessage("Cancelled.", false));
    });
    _scrollToBottom();
  }

  // ── Build ─────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: _buildAppBar(),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: _messages.isEmpty
                  ? _buildEmptyState()
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                      itemCount: _messages.length,
                      itemBuilder: (context, index) =>
                          _buildMessageTile(_messages[index]),
                    ),
            ),
            if (_loading) _buildTypingIndicator(),
            _buildInputBar(),
          ],
        ),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return PreferredSize(
      preferredSize: const Size.fromHeight(64),
      child: Container(
        decoration: BoxDecoration(
          color: _surface,
          border: const Border(bottom: BorderSide(color: _border, width: 1)),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                // Logo / Avatar
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [_accent, _accentEnd],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.psychology_rounded,
                      color: Colors.white, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text("PocketMind",
                          style: GoogleFonts.inter(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: Colors.white)),
                      Text(
                          _mode == ChatMode.assistant
                              ? "AI Assistant"
                              : "Search Phone",
                          style: GoogleFonts.inter(
                              fontSize: 11,
                              color: _accent,
                              fontWeight: FontWeight.w500)),
                    ],
                  ),
                ),
                // Mode switcher button
                GestureDetector(
                  onTap: _showModeSheet,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: _surface2,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: _border),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          _mode == ChatMode.assistant
                              ? Icons.smart_toy_outlined
                              : Icons.manage_search_rounded,
                          size: 14,
                          color: _accent,
                        ),
                        const SizedBox(width: 4),
                        Text("Mode",
                            style: GoogleFonts.inter(
                                fontSize: 12,
                                color: _textSec,
                                fontWeight: FontWeight.w500)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: SingleChildScrollView(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [_accent, _accentEnd],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                      color: _accent.withOpacity(0.4),
                      blurRadius: 24,
                      offset: const Offset(0, 8)),
                ],
              ),
              child: const Icon(Icons.psychology_rounded,
                  color: Colors.white, size: 36),
            ),
            const SizedBox(height: 20),
            Text("PocketMind Assistant",
                style: GoogleFonts.inter(
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    color: Colors.white)),
            const SizedBox(height: 8),
            Text("Ask me to manage your files,\nfind documents or search photos.",
                textAlign: TextAlign.center,
                style: GoogleFonts.inter(fontSize: 14, color: _textSec, height: 1.6)),
            const SizedBox(height: 32),
            _suggestionChip("📁  Scan my downloads folder"),
            const SizedBox(height: 8),
            _suggestionChip("🔍  Find DS Question Bank"),
            const SizedBox(height: 8),
            _suggestionChip("📊  Storage insights for DCIM"),
          ],
        ),
      ),
    );
  }

  Widget _suggestionChip(String label) {
    return GestureDetector(
      onTap: () {
        _controller.text =
            label.replaceAll(RegExp(r'^[\p{Emoji}\s]+', unicode: true), '').trim();
        _sendMessage();
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: _surface2,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: _border),
        ),
        child: Text(label,
            style:
                GoogleFonts.inter(fontSize: 13, color: _textSec)),
      ),
    );
  }

  Widget _buildMessageTile(ChatMessage msg) {
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.82,
        ),
        child: msg.isUser ? _userBubble(msg) : _aiBubble(msg),
      ),
    );
  }

  Widget _userBubble(ChatMessage msg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [_accent, _accentEnd],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(18),
          topRight: Radius.circular(18),
          bottomLeft: Radius.circular(18),
          bottomRight: Radius.circular(4),
        ),
        boxShadow: [
          BoxShadow(
              color: _accent.withOpacity(0.3),
              blurRadius: 12,
              offset: const Offset(0, 4)),
        ],
      ),
      child: Text(msg.text,
          style: GoogleFonts.inter(
              fontSize: 14, color: Colors.white, height: 1.5)),
    );
  }

  Widget _aiBubble(ChatMessage msg) {
    final showButtons = msg.pendingAction != null && !msg.resolved;
    final hasFiles = msg.filePaths != null && msg.filePaths!.isNotEmpty;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(4),
          topRight: Radius.circular(18),
          bottomLeft: Radius.circular(18),
          bottomRight: Radius.circular(18),
        ),
        border: Border.all(color: _border),
        boxShadow: const [
          BoxShadow(color: Color(0x1A000000), blurRadius: 8, offset: Offset(0, 2)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Message text
          if (msg.text.isNotEmpty || msg.isStreaming)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (!msg.isUser) ...[
                  Container(
                    width: 24,
                    height: 24,
                    margin: const EdgeInsets.only(right: 10, top: 1),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                          colors: [_accent, _accentEnd]),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.psychology_rounded,
                        size: 12, color: Colors.white),
                  ),
                ],
                Expanded(
                  child: Text(
                    msg.text.isEmpty && msg.isStreaming ? "..." : msg.text,
                    style: GoogleFonts.inter(
                        fontSize: 14, color: Colors.white, height: 1.6),
                  ),
                ),
              ],
            ),
          // File paths
          if (hasFiles) ...[
            if (msg.text.isNotEmpty) const SizedBox(height: 12),
            ...msg.filePaths!.asMap().entries.map((entry) =>
                _fileResultCard(entry.value, entry.key)),
          ],
          // Confirm/Cancel buttons
          if (showButtons) ...[
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: _gradientButton(
                    label: "Confirm",
                    icon: Icons.check_rounded,
                    onTap: () => _confirmAction(msg),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _outlineButton(
                    label: "Cancel",
                    onTap: () => _cancelAction(msg),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _fileResultCard(String path, int index) {
    final name = path.split('/').last;
    final ext = name.contains('.') ? name.split('.').last.toLowerCase() : '';
    final icon = _iconForExt(ext);
    final iconColor = _colorForExt(ext);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: _surface2,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _border),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, size: 18, color: iconColor),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    style: GoogleFonts.inter(
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                        color: Colors.white),
                    overflow: TextOverflow.ellipsis),
                const SizedBox(height: 2),
                Text(path,
                    style:
                        GoogleFonts.inter(fontSize: 10, color: _textSec),
                    overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: () => _openFile(path),
            child: Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [_accent, _accentEnd],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text("Open",
                  style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: Colors.white)),
            ),
          ),
        ],
      ),
    );
  }

  IconData _iconForExt(String ext) {
    switch (ext) {
      case 'pdf': return Icons.picture_as_pdf_rounded;
      case 'docx':
      case 'doc': return Icons.description_rounded;
      case 'xlsx':
      case 'csv': return Icons.table_chart_rounded;
      case 'pptx': return Icons.slideshow_rounded;
      case 'jpg':
      case 'jpeg':
      case 'png': return Icons.image_rounded;
      case 'mp4':
      case 'mkv': return Icons.videocam_rounded;
      case 'mp3':
      case 'opus':
      case 'm4a': return Icons.audiotrack_rounded;
      default: return Icons.insert_drive_file_rounded;
    }
  }

  Color _colorForExt(String ext) {
    switch (ext) {
      case 'pdf': return const Color(0xFFFF6B6B);
      case 'docx':
      case 'doc': return const Color(0xFF4ECDC4);
      case 'xlsx':
      case 'csv': return const Color(0xFF51CF66);
      case 'pptx': return const Color(0xFFFF9F43);
      case 'jpg':
      case 'jpeg':
      case 'png': return const Color(0xFF748FFC);
      case 'mp4':
      case 'mkv': return const Color(0xFFDA77F2);
      case 'mp3':
      case 'opus':
      case 'm4a': return const Color(0xFFFF6DAF);
      default: return _textSec;
    }
  }

  Widget _gradientButton(
      {required String label,
      required IconData icon,
      required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
              colors: [_accent, _accentEnd],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 14, color: Colors.white),
            const SizedBox(width: 6),
            Text(label,
                style: GoogleFonts.inter(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Colors.white)),
          ],
        ),
      ),
    );
  }

  Widget _outlineButton(
      {required String label, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: _border),
        ),
        child: Center(
          child: Text(label,
              style: GoogleFonts.inter(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: _textSec)),
        ),
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.only(left: 20, bottom: 8),
      child: Row(
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              gradient:
                  const LinearGradient(colors: [_accent, _accentEnd]),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.psychology_rounded,
                size: 12, color: Colors.white),
          ),
          const SizedBox(width: 10),
          _PulsingDots(controller: _loadingController),
        ],
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 20),
      decoration: BoxDecoration(
        color: _surface,
        border: const Border(top: BorderSide(color: _border, width: 1)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Mode button
          GestureDetector(
            onTap: _showModeSheet,
            child: Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: _surface2,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: _border),
              ),
              child: Icon(
                _mode == ChatMode.assistant
                    ? Icons.smart_toy_outlined
                    : Icons.manage_search_rounded,
                color: _accent,
                size: 20,
              ),
            ),
          ),
          const SizedBox(width: 10),
          // Text field
          Expanded(
            child: Container(
              constraints: const BoxConstraints(maxHeight: 120),
              decoration: BoxDecoration(
                color: _surface2,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: _border),
              ),
              child: TextField(
                controller: _controller,
                style: GoogleFonts.inter(fontSize: 14, color: Colors.white),
                maxLines: null,
                decoration: InputDecoration(
                  hintText: _mode == ChatMode.searchPhone
                      ? "Search your documents..."
                      : "Ask me anything...",
                  hintStyle:
                      GoogleFonts.inter(fontSize: 14, color: _textSec),
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 12),
                ),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
          ),
          const SizedBox(width: 10),
          // Send button
          GestureDetector(
            onTap: _sendMessage,
            child: Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [_accent, _accentEnd],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                      color: _accent.withOpacity(0.4),
                      blurRadius: 12,
                      offset: const Offset(0, 4)),
                ],
              ),
              child: const Icon(Icons.send_rounded,
                  color: Colors.white, size: 20),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Pulsing Dots Loading Indicator ─────────────────────────────────────────
class _PulsingDots extends StatelessWidget {
  final AnimationController controller;

  const _PulsingDots({required this.controller});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(3, (i) {
        return AnimatedBuilder(
          animation: controller,
          builder: (_, __) {
            final t = (controller.value - i * 0.15).clamp(0.0, 1.0);
            final scale = 0.5 + 0.5 * math.sin(t * math.pi);
            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 3),
              width: 7,
              height: 7,
              decoration: BoxDecoration(
                color: _accent.withOpacity(0.4 + 0.6 * scale),
                shape: BoxShape.circle,
              ),
            );
          },
        );
      }),
    );
  }
}
