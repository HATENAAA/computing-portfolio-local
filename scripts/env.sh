# Standard local paths, Homebrew versions, and an existing IntelliJ toolchain.
portfolio_root="$PWD"
export PATH="$portfolio_root/.tools/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
portfolio_brew=''
for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
  if [ -x "$candidate" ]; then portfolio_brew="$candidate"; break; fi
done
if [ -n "$portfolio_brew" ]; then
  portfolio_prefix="$("$portfolio_brew" --prefix)"
  export PATH="$portfolio_prefix/opt/node@24/bin:$portfolio_prefix/opt/python@3.12/bin:$portfolio_prefix/opt/python@3.12/libexec/bin:$portfolio_prefix/bin:$PATH"
  if [ -x "$portfolio_prefix/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home/bin/java" ]; then
    export JAVA_HOME="$portfolio_prefix/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
  fi
fi
if [ -z "${JAVA_HOME:-}" ] && [ -x '/Applications/IntelliJ IDEA.app/Contents/jbr/Contents/Home/bin/java' ]; then
  export JAVA_HOME='/Applications/IntelliJ IDEA.app/Contents/jbr/Contents/Home'
fi
if [ -n "${JAVA_HOME:-}" ]; then export PATH="$JAVA_HOME/bin:$PATH"; fi
if ! command -v mvn >/dev/null && [ -x '/Applications/IntelliJ IDEA.app/Contents/plugins/maven/lib/maven3/bin/mvn' ]; then
  export PATH="/Applications/IntelliJ IDEA.app/Contents/plugins/maven/lib/maven3/bin:$PATH"
fi
